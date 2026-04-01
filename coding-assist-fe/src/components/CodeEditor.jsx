import Editor from "@monaco-editor/react";
import { useEffect } from "react";

export default function CodeEditor({ code, onChange, onRunCode, onResetCode }) {
  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        onRunCode();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onRunCode]);

  return (
    <div className="editorBlock">
      <div className="editorActions">
        <button className="chipButton" onClick={onResetCode}>
          Reset to Starter
        </button>
        <span className="muted">Run shortcut: Ctrl/Cmd + Enter</span>
      </div>
      <div className="editorContainer">
      <Editor
        height="100%"
        defaultLanguage="python"
        value={code}
        onChange={(value) => onChange(value ?? "")}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          wordWrap: "on",
          scrollBeyondLastLine: false,
        }}
      />
      </div>
    </div>
  );
}
