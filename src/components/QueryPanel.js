import React, {useState} from "react";
import { Stack, TextField, Button } from "@mui/material";

export default function QueryPanel({setResults}){
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try{
      const res = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({query: q})
      });
      const data = await res.json();
      setResults(data);
    }catch(err){
      setResults({error: String(err)});
    }finally{
      setLoading(false);
    }
  };

  const onKey = (e) => { if(e.key === "Enter") submit(); };
  return (
    <Stack spacing={2} direction={{ xs: "column", sm: "row" }}>
      <TextField
        placeholder="e.g. Show me all Python developers in Engineering"
        value={q}
        onChange={(e)=>setQ(e.target.value)}
        onKeyDown={onKey}
        fullWidth
        size="small"
      />
      <Button variant="contained" onClick={submit} disabled={loading}>{loading ? "Running..." : "Run Query"}</Button>
    </Stack>
  );
}
