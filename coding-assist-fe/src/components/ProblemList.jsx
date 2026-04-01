export default function ProblemList({
  problems,
  activeProblemId,
  onSelectProblem,
  loading,
  searchQuery,
  onSearchChange,
  difficultyFilter,
  onDifficultyChange,
  attemptCounts,
}) {
  return (
    <aside className="panel">
      <h2 className="panelTitle">Problems</h2>
      <input
        className="searchInput"
        placeholder="Search problems..."
        value={searchQuery}
        onChange={(event) => onSearchChange(event.target.value)}
      />
      <div className="filterRow">
        {["all", "easy", "medium", "hard"].map((level) => (
          <button
            key={level}
            className={`chipButton ${difficultyFilter === level ? "activeChip" : ""}`}
            onClick={() => onDifficultyChange(level)}
          >
            {level}
          </button>
        ))}
      </div>
      {loading ? (
        <p className="muted">Loading problems...</p>
      ) : (
        <ul className="problemList">
          {problems.map((problem) => (
            <li key={problem.id}>
              <button
                className={`problemItem ${
                  problem.id === activeProblemId ? "active" : ""
                }`}
                onClick={() => onSelectProblem(problem.id)}
              >
                <span>
                  {problem.title}
                  {attemptCounts[problem.id] ? (
                    <small className="attemptCount"> · attempted {attemptCounts[problem.id]}x</small>
                  ) : null}
                </span>
                <small className={`tag ${problem.difficulty}`}>
                  {problem.difficulty}
                </small>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
