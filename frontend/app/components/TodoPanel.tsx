"use client";

import { useState, useEffect } from "react";
import { CheckSquare, Square, Trash2, Loader2, Clock } from "lucide-react";
import { api, TodoItem } from "../lib/api";
import EvidenceList from "./EvidenceList";

interface TodoPanelProps {
  sessionId: string;
}

export default function TodoPanel({ sessionId }: TodoPanelProps) {
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedTodo, setExpandedTodo] = useState<string | null>(null);

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
    <div className="bg-[#2e6a4f] rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Auto-Generated Todos</h2>
        <button
          onClick={handleGenerateTodos}
          disabled={loading}
          className="bg-[#256055] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#1e5249] disabled:bg-gray-500 flex items-center"
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
          <p className="text-green-100 text-center py-8">
            Click "Generate Todos" to extract action items from the meeting
          </p>
        ) : (
          todos.map((todo) => (
            <div
              key={todo.todo_id}
              className={`border border-green-600 rounded-lg p-4 ${
                todo.completed ? "bg-gray-100 opacity-75" : "bg-white"
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
                    <button
                      onClick={() => handleDelete(todo.todo_id)}
                      className="text-gray-400 hover:text-red-600 ml-2"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
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
                      className="text-xs text-[#2e6a4f] hover:text-[#1e5249] font-medium"
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
          ))
        )}
      </div>
    </div>
  );
}
