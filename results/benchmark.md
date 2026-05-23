# Procedural-room benchmark

World size 9x7. Each row is one random room; the BFS-driven scripted agent runs to completion or `max_steps`.

| seed | reachable cells | plan steps | invalid actions | succeeded |
| ---: | ---: | ---: | ---: | :---: |
| 0 | 29 | 16 | 0 | yes |
| 1 | 31 | 17 | 0 | yes |
| 2 | 29 | 14 | 0 | yes |
| 3 | 31 | 11 | 0 | yes |
| 4 | 31 | 10 | 0 | yes |
| 5 | 29 | 13 | 0 | yes |
| 6 | 29 | 14 | 0 | yes |
| 7 | 31 | 13 | 0 | yes |
| 8 | 31 | 9 | 0 | yes |
| 9 | 31 | 12 | 0 | yes |
| 10 | 29 | 17 | 0 | yes |
| 11 | 31 | 11 | 0 | yes |
| 12 | 31 | 13 | 0 | yes |
| 13 | 31 | 13 | 0 | yes |
| 14 | 31 | 13 | 0 | yes |
| 15 | 29 | 19 | 0 | yes |
| 16 | 31 | 10 | 0 | yes |
| 17 | 29 | 12 | 0 | yes |
| 18 | 31 | 10 | 0 | yes |
| 19 | 29 | 16 | 0 | yes |

## Summary
- success rate: 20/20 (100.0%)
- mean steps per run: 13.2
- mean invalid actions per run: 0.00
