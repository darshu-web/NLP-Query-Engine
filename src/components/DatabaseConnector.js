import React, {useState} from "react";
import { TextField, Button, Stack, Alert } from "@mui/material";

export default function DatabaseConnector(){
  const [conn, setConn] = useState("");
  const [schema, setSchema] = useState(null);
  const [message, setMessage] = useState("");

  const handleConnect = async () => {
    setMessage("Connecting...");
    try {
      const res = await fetch("http://localhost:8000/api/schema/database", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({connection_string: conn})
      });
      const data = await res.json();
      if(data.schema){
        setSchema(data.schema);
        setMessage("Schema discovered");
      } else {
        setMessage("No schema returned");
      }
    } catch(err){
      setMessage("Error: " + String(err));
    }
  };

  return (
    <Stack spacing={2}>
      <TextField
        label="Connection string"
        value={conn}
        onChange={(e)=>setConn(e.target.value)}
        placeholder="sqlite:///./demo_db.sqlite or postgresql://user:pass@host/db"
        fullWidth
        size="small"
      />
      <Stack direction="row" spacing={1}>
        <Button variant="contained" onClick={handleConnect}>Connect & Analyze</Button>
        <Button variant="outlined" onClick={()=>setConn("sqlite:///./demo_db.sqlite")}>Use demo DB</Button>
      </Stack>
      {message && <Alert severity={message.toLowerCase().includes("error")?"error":"info"}>{message}</Alert>}
      {schema && (
        <pre style={{maxHeight:300,overflow:"auto", background:"#0f0f0f10", padding:10, borderRadius:8}}>
          {JSON.stringify(schema, null, 2)}
        </pre>
      )}
    </Stack>
  )
}
