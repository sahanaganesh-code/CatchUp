"use client";

import { useState } from "react";
import { Zap, Loader2, CheckCircle, XCircle } from "lucide-react";
import { api, ProposedAction } from "../lib/api";
import EvidenceList from "./EvidenceList";

interface ActionsPanelProps {
  sessionId: string;
}

const ACTION_ICONS = {
  notion_task: "📝",
  calendar_event: "📅",
  email_followup: "✉️",
  slides: "📊",
};

const ACTION_LABELS = {
  notion_task: "Notion Task",
  calendar_event: "Calendar Event",
  email_followup: "Email Follow-up",
  slides: "Slides",
};

export default function ActionsPanel({ sessionId }: ActionsPanelProps) {
  const [actions, setActions] = useState<ProposedAction[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedAction, setExpandedAction] = useState<string | null>(null);

  const handleProposeActions = async () => {
    setLoading(true);
    try {
      const proposedActions = await api.proposeActions(sessionId);
      setActions(proposedActions);
    } catch (error) {
      console.error("Error proposing actions:", error);
      alert("Error proposing actions");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAction = async (actionId: string, approved: boolean) => {
    try {
      await api.approveAction(actionId, approved);

      setActions(
        actions.map((action) =>
          action.action_id === actionId
            ? { ...action, approved, executed: approved }
            : action
        )
      );

      if (approved) {
        alert("Action approved and executed!");
      }
    } catch (error) {
      console.error("Error approving action:", error);
      alert("Error approving action");
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Zap className="w-5 h-5 text-purple-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-900">
            FlowPilot Actions
          </h2>
        </div>
        <button
          onClick={handleProposeActions}
          disabled={loading}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-300 flex items-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Proposing...
            </>
          ) : (
            "Propose Actions"
          )}
        </button>
      </div>

      <div className="space-y-4">
        {actions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            Click "Propose Actions" to generate action items
          </p>
        ) : (
          actions.map((action) => (
            <div
              key={action.action_id}
              className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-start flex-1">
                  <span className="text-2xl mr-3">
                    {ACTION_ICONS[action.action_type]}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">
                        {action.title}
                      </h3>
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                        {ACTION_LABELS[action.action_type]}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      {action.description}
                    </p>

                    {/* Evidence Toggle */}
                    <button
                      onClick={() =>
                        setExpandedAction(
                          expandedAction === action.action_id
                            ? null
                            : action.action_id
                        )
                      }
                      className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                    >
                      {expandedAction === action.action_id
                        ? "Hide Evidence"
                        : `Show Evidence (${action.evidence.length})`}
                    </button>

                    {expandedAction === action.action_id && (
                      <div className="mt-3">
                        <EvidenceList evidence={action.evidence} compact />
                      </div>
                    )}
                  </div>
                </div>

                {/* Status Badge */}
                {action.executed && (
                  <CheckCircle className="w-5 h-5 text-green-600 ml-2" />
                )}
                {action.approved && !action.executed && (
                  <Loader2 className="w-5 h-5 text-blue-600 ml-2 animate-spin" />
                )}
              </div>

              {/* Approval Buttons */}
              {!action.approved && !action.executed && (
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => handleApproveAction(action.action_id, true)}
                    className="flex-1 bg-green-600 text-white py-2 rounded-lg font-medium hover:bg-green-700 flex items-center justify-center"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve & Execute
                  </button>
                  <button
                    onClick={() =>
                      handleApproveAction(action.action_id, false)
                    }
                    className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-lg font-medium hover:bg-gray-300 flex items-center justify-center"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Reject
                  </button>
                </div>
              )}

              {action.executed && (
                <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-2">
                  <p className="text-sm text-green-800 font-medium">
                    ✓ Action executed successfully
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-xs text-yellow-800">
          ⚠️ <strong>Approval Required:</strong> Actions will only execute
          after you approve them. No action runs automatically.
        </p>
      </div>
    </div>
  );
}
