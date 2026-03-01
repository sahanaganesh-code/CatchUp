/**
 * Record microphone to WAV using Web Audio API (no MediaRecorder/webm).
 * Produces a valid WAV file that the backend can convert to LINEAR16 for Cloud STT.
 */

function floatTo16BitPCM(float32Array: Float32Array): ArrayBuffer {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);
  let offset = 0;
  for (let i = 0; i < float32Array.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

/** Returns true if the PCM buffer is effectively silent (no speech). */
function isPcmSilent(pcmChunks: ArrayBuffer[]): boolean {
  const totalLength = pcmChunks.reduce((acc, buf) => acc + buf.byteLength, 0);
  if (totalLength < 4000) return true;
  let maxAbs = 0;
  const step = Math.max(1, Math.floor(totalLength / 2 / 1000));
  for (const chunk of pcmChunks) {
    const view = new DataView(chunk);
    for (let i = 0; i < view.byteLength - 1; i += step) {
      const s = view.getInt16(i, true);
      const abs = s < 0 ? -s : s;
      if (abs > maxAbs) maxAbs = abs;
    }
  }
  return maxAbs < 200;
}

function buildWavBlob(pcmChunks: ArrayBuffer[], sampleRate: number, numChannels: number): Blob {
  const totalLength = pcmChunks.reduce((acc, buf) => acc + buf.byteLength, 0);
  const wav = new ArrayBuffer(44 + totalLength);
  const view = new DataView(wav);

  const writeStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  };
  const byteRate = sampleRate * numChannels * 2;
  const blockAlign = numChannels * 2;

  writeStr(0, "RIFF");
  view.setUint32(4, 36 + totalLength, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, 1, true);  // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true);  // bits per sample
  writeStr(36, "data");
  view.setUint32(40, totalLength, true);

  let offset = 44;
  for (const chunk of pcmChunks) {
    new Uint8Array(wav).set(new Uint8Array(chunk), offset);
    offset += chunk.byteLength;
  }
  return new Blob([wav], { type: "audio/wav" });
}

export interface WavRecorderCallbacks {
  onStart?: () => void;
  onStop?: () => void;
  onError?: (err: string) => void;
}

export class WavRecorder {
  private stream: MediaStream | null = null;
  private context: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private chunks: ArrayBuffer[] = [];
  private sampleRate = 16000;
  private numChannels = 1;
  private callbacks: WavRecorderCallbacks = {};

  async start(callbacks: WavRecorderCallbacks = {}): Promise<void> {
    this.callbacks = callbacks;
    this.chunks = [];
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.context = new Ctx();
      const ctx = this.context;
      if (ctx.state === "suspended") {
        await ctx.resume();
      }
      if (ctx.state !== "running") {
        await new Promise((r) => setTimeout(r, 50));
        await ctx.resume();
      }
      this.sampleRate = ctx.sampleRate;
      this.source = ctx.createMediaStreamSource(this.stream);
      this.processor = ctx.createScriptProcessor(4096, this.numChannels, 1);
      this.processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0);
        this.chunks.push(floatTo16BitPCM(input));
      };
      this.source.connect(this.processor);
      const gain = ctx.createGain();
      gain.gain.value = 0;
      this.processor.connect(gain);
      gain.connect(ctx.destination);
      this.callbacks.onStart?.();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Microphone access failed";
      this.callbacks.onError?.(msg);
      throw err;
    }
  }

  /** Number of PCM chunks recorded so far (for live segment upload). */
  getChunkCount(): number {
    return this.chunks.length;
  }

  /**
   * Build a WAV blob from chunks [fromIndex..end] for live transcription.
   * Returns null if range is too short (< ~1 sec) or invalid.
   */
  buildWavFromChunkRange(fromIndex: number): Blob | null {
    if (fromIndex < 0 || fromIndex >= this.chunks.length) return null;
    const slice = this.chunks.slice(fromIndex);
    if (slice.length < 10) return null;
    return buildWavBlob(slice, this.sampleRate, this.numChannels);
  }

  stop(): Blob | null {
    try {
      if (this.processor) {
        this.processor.disconnect();
        this.processor = null;
      }
      if (this.source) {
        this.source.disconnect();
        this.source = null;
      }
      if (this.context) {
        this.context.close();
        this.context = null;
      }
      this.stream?.getTracks().forEach((t) => t.stop());
      this.stream = null;
      this.callbacks.onStop?.();

      if (this.chunks.length === 0) return null;
      if (isPcmSilent(this.chunks)) return null;
      return buildWavBlob(this.chunks, this.sampleRate, this.numChannels);
    } finally {
      this.chunks = [];
    }
  }
}
