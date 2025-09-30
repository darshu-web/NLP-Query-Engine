import React, {useState} from "react";
import { Stack, Button, Alert, LinearProgress, Typography } from "@mui/material";

export default function DocumentUploader(){
  const [files, setFiles] = useState(null);
  const [job, setJob] = useState(null);
  const [status, setStatus] = useState(null);

  const handleUpload = async () => {
    if(!files || files.length===0) return;
    const fd = new FormData();
    for(const f of files){
      fd.append("files", f);
    }
    const res = await fetch("http://localhost:8000/api/ingest/documents", {
      method: "POST",
      body: fd
    });
    const data = await res.json();
    setJob(data.job_id);
    setStatus("Processing started");
  };

  const checkStatus = async () => {
    if(!job) return;
    const res = await fetch(`http://localhost:8000/api/ingest/status/${job}`);
    const data = await res.json();
    setStatus(JSON.stringify(data));
  };

  return (
    <Stack spacing={2}>
      <input type="file" multiple onChange={(e)=>setFiles(e.target.files)} />
      <Stack direction="row" spacing={1}>
        <Button variant="contained" onClick={handleUpload}>Upload & Index</Button>
        <Button variant="outlined" onClick={checkStatus} disabled={!job}>Check Status</Button>
      </Stack>
      {status && <Alert severity="info">{typeof status === "string" ? status : JSON.stringify(status)}</Alert>}
      {job && <Typography variant="caption">Job: {job}</Typography>}
      {status && String(status).includes("processed") && <LinearProgress />}
    </Stack>
  );
}
