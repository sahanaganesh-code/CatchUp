"use client";

import { useState, useEffect } from "react";
import { CheckSquare, Square, Trash2, Loader2, Clock, Edit2, Save, X } from "lucide-react";
import { api, TodoItem } from "../lib/api";
import EvidenceList from "./EvidenceList";

interface TodoPanelProps {
  sessionId: string;
}

interface EditForm {
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
  due_date: string;
}

export default function TodoPanel({ sessionId }: TodoPanelProps) {
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedTodo, setExpandedTodo] = useState<string | null>(null);
  const [editingTodoId, setEditingTodoId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getTodos(sessionId).then(setTodos).catch((error) => {
      console.error("Error loading todos:", error);
    });
  }, [sessionId]);

  const handleGenerateTodos = async () => {
    setLoading(true);
    try {
      const generatedTodos = await api.generateTodos(sessionId);
      setTodos(generatedTodos);
    } catch (error) {
      console.error("Error generating todos:", error);
      alert("Error generating todos");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleComplete = async (todoId: string, completed: boolean) => {
    try {
      await api.completeTodo(todoId, !completed);
      setTodos(
        todos.map((t) =>
          t.todo_id === todoId ? { ...t, completed: !completed } : t
        )
      );
    } catch (error) {
      console.error("Error toggling todo:", error);
    }
  };

  const handleDelete = async (todoId: string) => {
    try {
      await api.deleteTodo(todoId);
      setTodos(todos.filter((t) => t.todo_id !== todoId));
    } catch (error) {
      console.error("Error deleting todo:", error);
    }
  };

  const handleEditStart = (todo: TodoItem) => {
    setEditingTodoId(todo.todo_id);
    setEditForm({
      title: todo.title,
      description: todo.description,
      priority: todo.priority,
      due_date: todo.due_date || "",
    });
  };

  const handleEditCancel = () => {
    setEditingTodoId(null);
    setEditForm(null);
  };

  const handleEditSave = async (todoId: string) => {
    if (!editForm) return;
    setSaving(true);
    try {
      const updated = await api.updateTodo(todoId, {
        title: editForm.title,
        description: editForm.description,
        priority: editForm.priority,
        due_date: editForm.due_date || undefined,
      });
      setTodos(todos.map((t) => (t.todo_id === todoId ? updated : t)));
      setEditingTodoId(null);
      setEditForm(null);
    } catch (error) {
      console.error("Error updating todo:", error);
      alert("Error updating todo");
    } finally {
      setSaving(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-600 bg-red-50 border-red-200";
      case "medium":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "low":
        return "text-green-600 bg-green-50 border-green-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Auto-Generated Todos</h2>
        <button
          onClick={handleGenerateTodos}
          disabled={loading}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:bg-gray-300 flex items-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            "Generate Todos"
          )}
        </button>
      </div>

      <div className="space-y-3">
        {todos.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            Click "Generate Todos" to extract action items from the meeting
          </p>
        ) : (
          todos.map((todo) => {
            const isEditing = editingTodoId === todo.todo_id;

            if (isEditing && editForm) {
              return (
                <div
                  key={todo.todo_id}
                  className="border border-indigo-300 rounded-lg p-4 bg-indigo-50"
                >
                  <input
                    type="text"
                    value={editForm.title}
                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    placeholder="Todo title..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <textarea
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    placeholder="Description..."
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <select
                      value={editForm.priority}
                      onChange={(e) =>
                        setEditForm({ ...editForm, priority: e.target.value as "low" | "medium" | "high" })
                      }
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                    <input
                      type="date"
                      value={editForm.due_date}
                      onChange={(e) => setEditForm({ ...editForm, due_date: e.target.value })}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEditSave(todo.todo_id)}
                      disabled={saving || !editForm.title.trim()}
                      className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:bg-gray-300 flex items-center"
                    >
                      {saving ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Save className="w-4 h-4 mr-2" />
                          Save
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleEditCancel}
                      className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-300"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={todo.todo_id}
                className={`border rounded-lg p-4 ${
                  todo.completed ? "bg-gray-50 opacity-75" : "bg-white"
                }`}
              >
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => handleToggleComplete(todo.todo_id, todo.completed)}
                    className="mt-1"
                  >
                    {todo.completed ? (
                      <CheckSquare className="w-5 h-5 text-green-600" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>

                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3
                          className={`font-semibold ${
                            todo.completed
                              ? "line-through text-gray-500"
                              : "text-gray-900"
                          }`}
                        >
                          {todo.title}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {todo.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-1 ml-2">
                        <button
                          onClick={() => handleEditStart(todo)}
                          className="text-gray-400 hover:text-indigo-600 p-1"
                          title="Edit todo"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(todo.todo_id)}
                          className="text-gray-400 hover:text-red-600 p-1"
                          title="Delete todo"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <span
                        className={`px-2 py-1 rounded border ${getPriorityColor(
                          todo.priority
                        )}`}
                      >
                        {todo.priority.toUpperCase()}
                      </span>
                      {todo.due_date && (
                        <span className="flex items-center text-gray-600">
                          <Clock className="w-3 h-3 mr-1" />
                          Due: {todo.due_date}
                        </span>
                      )}
                    </div>

                    {/* Evidence */}
                    <div className="mt-3">
                      <button
                        onClick={() =>
                          setExpandedTodo(
                            expandedTodo === todo.todo_id ? null : todo.todo_id
                          )
                        }
                        className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                      >
                        {expandedTodo === todo.todo_id
                          ? "Hide Evidence"
                          : `Show Evidence (${todo.evidence.length})`}
                      </button>

                      {expandedTodo === todo.todo_id && (
                        <div className="mt-2">
                          <EvidenceList evidence={todo.evidence} compact />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
