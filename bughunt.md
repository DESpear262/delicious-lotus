# Bughunt Notes

This document transcribes the handwritten notes from the front-end bughunt conducted on November 15, 2025 so that the issues can be triaged inside the backlog.

## Raw Transcription

- Check default generation time (forced by front-end, disregard).
- Parallelize generations.
- Replicate call webhook when done?
- Save generations to S3 and call other modules to handle generations.
- Arbitrary char limit needs to go away.
- Sending requests fails with 404 (request to `/ai/v1/generations`).
- Previous draft checker needs more helpful messages on buttons.
- History button gives JS but not HTTP errors.
- Logo uploads fail 404 at `api/v1/assets/upload`.
- Front end looks like ass, make it pretty.
- Check gun ads.

