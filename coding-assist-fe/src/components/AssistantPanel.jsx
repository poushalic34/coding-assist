import { useState } from "react";

export default function AssistantPanel({
  onAskHint,
  onEscalateHint,
  onClearHints,
  latestVerdict,
  loading,
  history,
  coachingMode,
  onCoachingModeChange,
  focusArea,
  onFocusAreaChange,
}) {
  const [question, setQuestion] = useState("");
  const focusOptions = [
    { id: "general", label: "General" },
    { id: "debugging", label: "Debugging" },
    { id: "edge_cases", label: "Edge cases" },
    { id: "complexity", label: "Complexity" },
    { id: "dry_run", label: "Dry run" },
  ];

  const submit = () => {
    if (!question.trim()) {
      return;
    }
    onAskHint(question.trim());
    setQuestion("");
  };

  return (
    <section className="panel assistantPanel">
      <h2 className="panelTitle">Agent Coach</h2>
      <p className="muted">Latest verdict: {latestVerdict ?? "Not run yet"}</p>
      <label className="muted controlLabel">
        Coaching mode
        <select
          className="modeSelect"
          value={coachingMode}
          onChange={(event) => onCoachingModeChange(event.target.value)}
        >
          <option value="strict">Strict</option>
          <option value="balanced">Balanced</option>
          <option value="fast-track">Fast-track</option>
        </select>
      </label>
      <div className="filterRow">
        {focusOptions.map((option) => (
          <button
            key={option.id}
            className={`chipButton ${focusArea === option.id ? "activeChip" : ""}`}
            onClick={() => onFocusAreaChange(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>
      <div className="filterRow">
        <button className="chipButton" onClick={() => onAskHint("Give me the next smallest hint only.")}>
          Next smallest hint
        </button>
        <button className="chipButton" onClick={() => onAskHint("Where might my logic fail for edge cases?")}>
          Debug failure
        </button>
        <button className="chipButton" onClick={() => onAskHint("How can I optimize runtime and memory?")}>
          Optimize complexity
        </button>
        <button className="chipButton" onClick={onEscalateHint}>
          Escalate hint
        </button>
      </div>
      <textarea
        className="inputArea"
        rows={4}
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ask for guidance, optimization ideas, or debugging help..."
      />
      <div className="filterRow">
        <button className="primaryButton" onClick={submit} disabled={loading}>
          {loading ? "Thinking..." : "Get Hint"}
        </button>
        <button className="chipButton" onClick={onClearHints} disabled={loading || !history.length}>
          Clear hints
        </button>
      </div>

      <div className="assistantHistory">
        {history.length ? (
          [...history].reverse().map((entry, index) => (
            <div key={`${entry.question}-${index}`} className="hintCard">
              <p className="muted">
                Q: {entry.question}
                <span className="sourceBadge">{entry.response.source}</span>
              </p>
              <p className="muted">Level: {entry.response.hint_level}</p>
              <p className="muted">Next: {entry.response.next_hint_level}</p>
              <p className="muted">Confidence: {Math.round((entry.response.confidence ?? 0) * 100)}%</p>
              <h3>Guided hint</h3>
              <p>{entry.response.guided_hint}</p>
              <h3>Strategy</h3>
              <p>{entry.response.strategy}</p>
              <h3>Complexity</h3>
              <p>{entry.response.complexity_suggestion}</p>
            </div>
          ))
        ) : (
          <p className="muted">Ask a question to start guided hints.</p>
        )}
      </div>
    </section>
  );
}
