// src/api/jobs.js
import client from "./client";

export async function fetchJobs() {
  const response = await client.post("/jobs/fetch");
  return response.data;
}

export async function getJobs(page = 1, perPage = 50) {
  const response = await client.get("/jobs", {
    params: { page, per_page: perPage },
  });
  return response.data;
}
