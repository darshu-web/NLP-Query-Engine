import React from "react";
import { Typography, Alert, Stack, Table, TableBody, TableCell, TableHead, TableRow, Card, CardContent } from "@mui/material";

export default function ResultsView({results}){
  if(!results) return null;
  if(results.error) return <Alert severity="error">{results.error}</Alert>;

  const rows = Array.isArray(results.results) ? results.results : [];
  const docHits = Array.isArray(results.docs) ? results.docs : [];

  // derive table columns
  const columns = rows.length ? Object.keys(rows[0]) : [];

  return (
    <Stack spacing={2}>
      <Typography variant="body2">Type: {results.type}</Typography>
      <Typography variant="body2">Metrics: {JSON.stringify(results.metrics)}</Typography>

      {rows.length > 0 && (
        <div style={{overflowX:"auto"}}>
          <Typography variant="subtitle1" gutterBottom>Table Results</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                {columns.map((c)=>(<TableCell key={c}>{c}</TableCell>))}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r, i)=>(
                <TableRow key={i}>
                  {columns.map((c)=>(<TableCell key={c}>{String(r[c])}</TableCell>))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {docHits.length > 0 && (
        <div>
          <Typography variant="subtitle1" gutterBottom>Document Hits</Typography>
          <Stack spacing={1}>
            {docHits.map((d, idx)=>(
              <Card key={idx} variant="outlined">
                <CardContent>
                  <Typography variant="caption">Score: {d.score.toFixed(3)} • Source: {d.source}</Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {d.text.slice(0, 400)}{d.text.length>400?"...":""}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </div>
      )}
    </Stack>
  );
}
