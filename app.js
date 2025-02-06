import React, { useState } from "react";
import axios from "axios";

function App() {
  const [twitterHandle, setTwitterHandle] = useState("");
  const [company, setCompany] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchInsights = async () => {
    if (!twitterHandle || !company) {
      alert("Please enter both Twitter handle and company name.");
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.get(`http://127.0.0.1:8000/fetch-insights`, {
        params: { twitter_handle: twitterHandle, company: company }
      });
      setData(response.data);
    } catch (error) {
      console.error("Error fetching insights:", error);
    }
    
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>Twitter & Company Insights</h1>
      
      <div className="input-section">
        <input 
          type="text" 
          placeholder="Enter Twitter Handle (e.g. elonmusk)" 
          value={twitterHandle} 
          onChange={(e) => setTwitterHandle(e.target.value)}
        />
        <input 
          type="text" 
          placeholder="Enter Company Name (e.g. Tesla)" 
          value={company} 
          onChange={(e) => setCompany(e.target.value)}
        />
        <button onClick={fetchInsights} disabled={loading}>
          {loading ? "Fetching..." : "Get Insights"}
        </button>
      </div>

      {data && (
        <div className="results">
          <h2>Twitter Insights for @{data.twitter_handle}</h2>
          <ul>
            {data.twitter_insights.map((tweet, index) => (
              <li key={index}>{tweet}</li>
            ))}
          </ul>

          <h2>Company Pain Points for {data.company}</h2>
          <ul>
            {data.company_pain_points.map((issue, index) => (
              <li key={index}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;