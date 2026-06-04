export type AppAccessState =
  | 'anonymous'
  | 'authenticated-no-sleeper'
  | 'sleeper-read-only'
  | 'sleeper-write';