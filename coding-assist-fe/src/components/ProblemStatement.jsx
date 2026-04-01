export default function ProblemStatement({ problem, loading }) {
  return (
    <section className="panel">
      <h2 className="panelTitle">Problem</h2>
      {loading ? (
        <p className="muted">Loading statement...</p>
      ) : problem ? (
        <>
          <h3 className="problemTitle">{problem.title}</h3>
          <p className="muted">
            Difficulty: <span className={`tag ${problem.difficulty}`}>{problem.difficulty}</span>
          </p>
          {problem.topics?.length ? (
            <p className="muted">Topics: {problem.topics.join(", ")}</p>
          ) : null}
          <p className="description">{problem.description}</p>
          {problem.constraints?.length ? (
            <div className="metaSection">
              <h4>Constraints</h4>
              <ul>
                {problem.constraints.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {problem.learning_objectives?.length ? (
            <div className="metaSection">
              <h4>Learning Objectives</h4>
              <ul>
                {problem.learning_objectives.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : (
        <p className="muted">Select a problem to begin.</p>
      )}
    </section>
  );
}
