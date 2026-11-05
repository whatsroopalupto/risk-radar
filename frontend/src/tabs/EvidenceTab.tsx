import { useState } from "react";
import { apiClient } from "../api/client";
import { Search } from "lucide-react";

interface EvidenceResult {
  dataset: string; mode: string; model: string | null; notice: string;
  paragraphs: { text: string; citations: string[] }[];
  sources: { id: string; title: string; source: string; published_at: string; url: string | null; evidence: string }[];
}
export default function EvidenceTab() {
  const [question, setQuestion] = useState("What evidence concerns oil shipping through Hormuz?");
  const [generate, setGenerate] = useState(true);
  const [result, setResult] = useState<EvidenceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return <section className="evidence-tab">
    <h2>Evidence &amp; Context</h2>
    <p>Search retained reporting for the selected dataset. Answers cite retrieved sources and do not change risk scores.</p>
    <form className="evidence-search-form" onSubmit={async (event) => {
      event.preventDefault(); setLoading(true); setError(null);
      try { setResult(await apiClient<EvidenceResult>("/api/evidence/ask", { method: "POST", body: JSON.stringify({ question, generate }) })); }
      catch { setError("Evidence request failed. Please try again."); }
      finally { setLoading(false); }
    }}>
      <label htmlFor="evidence-question" className="visually-hidden">
        Question
      </label>

      <div className="evidence-search-input">
        <Search size={17} aria-hidden="true" />
        <input
          id="evidence-question"
          value={question}
          minLength={3}
          maxLength={500}
          required
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What evidence concerns oil shipping through Hormuz?"
        />
      </div>
      <div className="evidence-form-actions">
        <label>
          <input
            type="checkbox"
            checked={generate}
            onChange={(event) => setGenerate(event.target.checked)}
          />
          Generate a cited summary when the AI service is available
        </label>

        <button disabled={loading} type="submit">
          {loading ? "Retrieving evidence..." : "Find evidence"}
        </button>
      </div>
    </form>
    {error && <p role="alert">{error}</p>}
    {result && <article className="evidence-results-panel" aria-live="polite">
      <h3>{result.mode === "rag" ? "Generated answer with retrieved evidence" : "Retrieved evidence"}</h3>
      <p>Dataset: {result.dataset} · {result.model ?? "No generated summary"}</p><p>{result.notice}</p>
      {result.paragraphs.map((paragraph, index) => <p key={index}>{paragraph.text}{" "}
        {paragraph.citations.map((id) => {
          const number = result.sources.findIndex((source) => source.id === id) + 1;
          return <a href={`#evidence-${number}`} key={id}>[{number}] </a>;
        })}</p>)}
      <h3>Sources</h3><ol>{result.sources.map((source, index) => <li key={source.id} id={`evidence-${index + 1}`}>
        {source.url ? <a href={source.url} target="_blank" rel="noopener noreferrer">{source.title}</a> : source.title}
        <p>{source.source} · Published {source.published_at}</p>
      </li>)}</ol>
    </article>}
  </section>;
}