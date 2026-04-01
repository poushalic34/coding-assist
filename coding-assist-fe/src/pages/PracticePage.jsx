import { useCallback, useEffect, useState } from "react";

import AssistantPanel from "../components/AssistantPanel";
import CodeEditor from "../components/CodeEditor";
import ProblemList from "../components/ProblemList";
import ProblemStatement from "../components/ProblemStatement";
import ResultPanel from "../components/ResultPanel";
import { api } from "../lib/api";

export default function PracticePage({ user, onLogout }) {
  const [allProblems, setAllProblems] = useState([]);
  const [problems, setProblems] = useState([]);
  const [activeProblemId, setActiveProblemId] = useState(null);
  const [activeProblem, setActiveProblem] = useState(null);

  const [code, setCode] = useState("");
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState("all");
  const [attemptCounts, setAttemptCounts] = useState(() => readJson("attemptCounts", {}));
  const [draftsByProblem, setDraftsByProblem] = useState(() => readJson("problemDrafts", {}));
  const [hintHistoryByProblem, setHintHistoryByProblem] = useState(() =>
    readJson("hintHistoryByProblem", {}),
  );
  const [conversationIdsByProblem, setConversationIdsByProblem] = useState(() =>
    readJson("conversationIdsByProblem", {}),
  );
  const [coachingMode, setCoachingMode] = useState("balanced");
  const [focusArea, setFocusArea] = useState("general");

  const [loadingProblems, setLoadingProblems] = useState(false);
  const [loadingProblemDetails, setLoadingProblemDetails] = useState(false);
  const [running, setRunning] = useState(false);
  const [gettingHint, setGettingHint] = useState(false);

  const activeHintHistory = hintHistoryByProblem[activeProblemId] ?? [];
  const activeConversationId = conversationIdsByProblem[activeProblemId] ?? null;

  useEffect(() => {
    const load = async () => {
      setLoadingProblems(true);
      try {
        const list = await api.listProblems();
        setAllProblems(list);
        setProblems(list);
        const storedProblemId = localStorage.getItem("lastProblemId");
        if (storedProblemId && list.some((item) => item.id === storedProblemId)) {
          setActiveProblemId(storedProblemId);
        } else if (list.length > 0) {
          setActiveProblemId(list[0].id);
        }
      } catch (error) {
        setRunError(error.message);
      } finally {
        setLoadingProblems(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    let nextProblems = [...allProblems];
    if (difficultyFilter !== "all") {
      nextProblems = nextProblems.filter((item) => item.difficulty === difficultyFilter);
    }
    if (searchQuery.trim()) {
      const lowered = searchQuery.trim().toLowerCase();
      nextProblems = nextProblems.filter((item) => item.title.toLowerCase().includes(lowered));
    }
    setProblems(nextProblems);
  }, [allProblems, difficultyFilter, searchQuery]);

  useEffect(() => {
    if (!activeProblemId && problems.length) {
      setActiveProblemId(problems[0].id);
      return;
    }
    if (activeProblemId && !problems.some((item) => item.id === activeProblemId) && problems.length) {
      setActiveProblemId(problems[0].id);
    }
  }, [activeProblemId, problems]);

  useEffect(() => {
    const loadProblem = async () => {
      if (!activeProblemId) {
        return;
      }
      setLoadingProblemDetails(true);
      setRunResult(null);
      setRunError("");
      try {
        const details = await api.getProblem(activeProblemId);
        setActiveProblem(details);
        localStorage.setItem("lastProblemId", activeProblemId);
        const storedDrafts = readJson("problemDrafts", {});
        setCode(storedDrafts[activeProblemId] ?? details.starter_code ?? "");
      } catch (error) {
        setRunError(error.message);
      } finally {
        setLoadingProblemDetails(false);
      }
    };
    loadProblem();
  }, [activeProblemId]);

  useEffect(() => {
    if (!activeProblemId || !activeProblem || activeProblem.id !== activeProblemId || loadingProblemDetails) {
      return;
    }
    if (draftsByProblem[activeProblemId] === code) {
      return;
    }
    const next = { ...draftsByProblem, [activeProblemId]: code };
    setDraftsByProblem(next);
    localStorage.setItem("problemDrafts", JSON.stringify(next));
  }, [activeProblemId, activeProblem, code, loadingProblemDetails, draftsByProblem]);

  const onRunCode = useCallback(async () => {
    if (!activeProblemId) {
      return;
    }
    setRunning(true);
    setRunError("");
    try {
      const result = await api.runSubmission({ problem_id: activeProblemId, code });
      setRunResult(result);
      setAttemptCounts((previous) => {
        const next = {
          ...previous,
          [activeProblemId]: (previous[activeProblemId] ?? 0) + 1,
        };
        localStorage.setItem("attemptCounts", JSON.stringify(next));
        return next;
      });
    } catch (error) {
      setRunError(error.message);
    } finally {
      setRunning(false);
    }
  }, [activeProblemId, code]);

  const onAskHint = async (question, options = {}) => {
    if (!activeProblemId) {
      return;
    }
    setGettingHint(true);
    setRunError("");
    try {
      const latestFailureSummary = runResult?.failed_case_summary
        ? `${runResult.failed_case_summary.scope}: ${runResult.failed_case_summary.message}`
        : null;
      const result = await api.getHint({
        problem_id: activeProblemId,
        code,
        latest_verdict: runResult?.verdict ?? "not_run",
        user_question: question,
        attempt_number: activeHintHistory.length + 1,
        latest_failure_summary: latestFailureSummary,
        coaching_mode: coachingMode,
        focus_area: focusArea,
        conversation_id: activeConversationId,
        requested_hint_level: options.requestedHintLevel ?? null,
      });
      if (result.conversation_id && !activeConversationId) {
        setConversationIdsByProblem((previous) => {
          const next = { ...previous, [activeProblemId]: result.conversation_id };
          localStorage.setItem("conversationIdsByProblem", JSON.stringify(next));
          return next;
        });
      }
      setHintHistoryByProblem((previous) => {
        const existing = previous[activeProblemId] ?? [];
        const next = {
          ...previous,
          [activeProblemId]: [...existing, { question, response: result }],
        };
        localStorage.setItem("hintHistoryByProblem", JSON.stringify(next));
        return next;
      });
    } catch (error) {
      setRunError(error.message);
    } finally {
      setGettingHint(false);
    }
  };

  const onResetCode = () => {
    if (!activeProblem) {
      return;
    }
    setCode(activeProblem.starter_code ?? "");
  };

  const onAskFailureHint = () => {
    if (!runResult?.failed_case_summary) {
      return;
    }
    onAskHint(
      `Help me debug this ${runResult.failed_case_summary.scope} failure: ${runResult.failed_case_summary.message}`,
    );
  };

  const onEscalateHint = () => {
    const nextHintLevel =
      activeHintHistory[activeHintHistory.length - 1]?.response?.next_hint_level ?? "next_step";
    onAskHint(`Please escalate one level to ${nextHintLevel} without giving full code.`, {
      requestedHintLevel: nextHintLevel,
    });
  };

  const onClearHints = () => {
    if (!activeProblemId) {
      return;
    }
    setHintHistoryByProblem((previous) => {
      const next = { ...previous };
      delete next[activeProblemId];
      localStorage.setItem("hintHistoryByProblem", JSON.stringify(next));
      return next;
    });
    setConversationIdsByProblem((previous) => {
      const next = { ...previous };
      delete next[activeProblemId];
      localStorage.setItem("conversationIdsByProblem", JSON.stringify(next));
      return next;
    });
  };

  return (
    <div className="appShell">
      <header className="header">
        <h1>Agentic Coding IDE</h1>
        <div className="headerActions">
          <span className="muted">{user?.email}</span>
          <button className="primaryButton" onClick={onRunCode} disabled={running}>
            {running ? "Running..." : "Run Code"}
          </button>
          <button className="chipButton" onClick={onLogout} type="button">
            Logout
          </button>
        </div>
      </header>

      <main className="layout">
        <ProblemList
          problems={problems}
          activeProblemId={activeProblemId}
          onSelectProblem={setActiveProblemId}
          loading={loadingProblems}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          difficultyFilter={difficultyFilter}
          onDifficultyChange={setDifficultyFilter}
          attemptCounts={attemptCounts}
        />

        <section className="centerColumn">
          <ProblemStatement problem={activeProblem} loading={loadingProblemDetails} />
          <CodeEditor
            code={code}
            onChange={setCode}
            onRunCode={onRunCode}
            onResetCode={onResetCode}
          />
          <ResultPanel result={runResult} error={runError} onAskFailureHint={onAskFailureHint} />
        </section>

        <AssistantPanel
          latestVerdict={runResult?.verdict}
          onAskHint={onAskHint}
          onEscalateHint={onEscalateHint}
          onClearHints={onClearHints}
          loading={gettingHint}
          history={activeHintHistory}
          coachingMode={coachingMode}
          onCoachingModeChange={setCoachingMode}
          focusArea={focusArea}
          onFocusAreaChange={setFocusArea}
        />
      </main>
    </div>
  );
}
function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

