# Profiling

## Profiling Command

- run `just profile`
- artifact: `monitoring/profiling/widget-routes.prof`

## When To Use It

- when widget-route latency regresses
- when request metrics or post-deploy checks suggest unexpected slowdown

## Evidence Path

- use `/metrics` to identify regressions first
- capture a fresh `widget-routes.prof` artifact with `just profile`
- inspect the artifact with standard Python profiling tools before changing runtime code
