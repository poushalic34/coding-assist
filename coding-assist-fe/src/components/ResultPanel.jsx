export default function ResultPanel({ result, error, onAskFailureHint }) {
  return (
    <section className="panel">
      <h2 className="panelTitle">Run Result</h2>
      {error ? <p className="errorText">{error}</p> : null}
      {!result ? (
        <p className="muted">Run your code to see verdict and test details.</p>
      ) : (
        <div className="resultCard">
          <p>
            <strong>Verdict:</strong> {result.verdict}
          </p>
          <p>
            <strong>Failure category:</strong> {result.failure_category ?? "none"}
          </p>
          <p>
            <strong>Passed:</strong> {result.passed_count} / {result.total_count}
          </p>
          <p>
            <strong>Runtime:</strong> {result.runtime_ms} ms
          </p>
          <p>
            <strong>Hidden tests passed:</strong> {result.hidden_passed_count ?? 0} /{" "}
            {result.hidden_total_count ?? 0}
          </p>
          {result.next_recommendation ? (
            <p>
              <strong>Next step:</strong> {result.next_recommendation}
            </p>
          ) : null}
          {result.error ? (
            <p>
              <strong>Error:</strong> {result.error}
            </p>
          ) : null}
          {result.sample_results?.length ? (
            <div className="sampleResults">
              <h3>Sample test breakdown</h3>
              <ul>
                {result.sample_results.map((item) => (
                  <li key={item.index} className={item.passed ? "passText" : "failText"}>
                    Sample #{item.index}: {item.passed ? "Passed" : "Failed"}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {result.failed_case_summary ? (
            <div className="failedCase">
              <p>
                <strong>Failure scope:</strong> {result.failed_case_summary.scope}
              </p>
              <p>
                <strong>Message:</strong> {result.failed_case_summary.message}
              </p>
              <p>
                <strong>Input:</strong>
              </p>
              <pre>{result.failed_case_summary.input ?? "Hidden test details not shown."}</pre>
              {result.failed_case_summary.expected_output ? (
                <p>
                  <strong>Expected:</strong> {result.failed_case_summary.expected_output}
                </p>
              ) : null}
              {result.failed_case_summary.actual_output ? (
                <p>
                  <strong>Actual:</strong> {result.failed_case_summary.actual_output}
                </p>
              ) : null}
              <button className="chipButton" onClick={onAskFailureHint}>
                Ask assistant about this failure
              </button>
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}
