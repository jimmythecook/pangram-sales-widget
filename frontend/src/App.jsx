import { useState } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [targetObjectDescription, setTargetObjectDescription] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [result, setResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    setResult(null)

    if (!url || !targetObjectDescription) {
      setError('Please enter both a URL and a target description.')
      setIsLoading(false)
      return
    }

    try {
      const payload = {
        url: url,
        target_object_description: targetObjectDescription,
      }
      if (username) payload.username = username
      if (password) payload.password = password

      const response = await fetch('/api/process-url', { // Assuming backend is on the same host, or configure proxy
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        let errorData
        try {
          errorData = await response.json()
        } catch (e) {
          // If parsing error JSON fails, use status text
          errorData = { detail: response.statusText }
        }
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      console.error("Error submitting form:", err)
      setError(err.message || 'Failed to process the request. Check console for details.')
    }
    setIsLoading(false)
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>HyperBrowser & Pangram Analyzer</h1>
      </header>
      <main>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="url">Target URL:</label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="targetObjectDescription">What to extract (e.g., "the main article text", "product price"): </label>
            <textarea
              id="targetObjectDescription"
              value={targetObjectDescription}
              onChange={(e) => setTargetObjectDescription(e.target.value)}
              placeholder="Describe the content you want to extract..."
              rows={3}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="username">Username (optional):</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username if required for URL"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password (optional):</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password if required for URL"
            />
          </div>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Processing...' : 'Process URL'}
          </button>
        </form>

        {error && (
          <div className="results-container error-message">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="results-container">
            <h3>Results</h3>
            <div className="result-section">
              <h4>HyperBrowser Outcome (Stub)</h4>
              <p>Status: {result.hyperbrowser_result?.status}</p>
              {result.hyperbrowser_result?.extracted_text && (
                <pre className="extracted-text">{result.hyperbrowser_result.extracted_text}</pre>
              )}
              {result.hyperbrowser_result?.error_message && (
                <p>Error: {result.hyperbrowser_result.error_message}</p>
              )}
            </div>
            <div className="result-section">
              <h4>Pangram Analysis (Stub)</h4>
              <p>Prediction: {result.pangram_analysis?.prediction}</p>
              <p>AI Likelihood: {result.pangram_analysis?.ai_likelihood !== undefined ? result.pangram_analysis.ai_likelihood.toFixed(2) : 'N/A'}</p>
              {result.pangram_analysis?.error_message && (
                <p>Error: {result.pangram_analysis.error_message}</p>
              )}
            </div>
            <div className="result-section">
                <h4>Overall</h4>
                <p>Status: {result.overall_status}</p>
                {result.error_message && (
                    <p>Overall Error: {result.error_message}</p>
                )}
            </div>
          </div>
        )}
      </main>
      <footer>
        <p>Pangram Sales Widget</p>
      </footer>
    </div>
  )
}

export default App
