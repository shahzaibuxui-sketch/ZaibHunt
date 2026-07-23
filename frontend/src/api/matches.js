// src/api/matches.js
import client from "./client";

export async function runMatching() {
  const response = await client.post("/matches/run");
  return response.data;
}

export async function getMatches() {
  const response = await client.get("/matches");
  return response.data;
}

export async function generateCoverLetter(matchId) {
  const response = await client.post(`/matches/${matchId}/cover-letter`);
  return response.data;
}
