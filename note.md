| model        | backend | time   | note                                           |
| ------------ | ------- | ------ | ---------------------------------------------- |
| InternVL3-2b | mps     | 65.60s |                                                |
| InternVL3-2b | mps     | 27.58s |                                                |
| InternVL3-2b | mps     | 52.70s | 输出 6 样食物                                  |
| InternVL3-2b | mps     | 39.52s | 更换 prompt 去掉 note                          |
| InternVL3-2b | mps     | 21.62s | 两样                                           |
| InternVL3-2b | cuda    | 17.52s | 两样                                           |
| InternVL3-2b | cuda    | 18.40s | 同上相同样本                                   |
| InternVL3-1b | mps     | 11.53s | 1b 模型,同上,无法理解中文名                    |
| InternVL3-1b | cuda    | 14.52s | 1b 模型同上,无法理解中文名                     |
| InternVL3-1b | cuda    | 14.14s | 指令遵循能力不够,推理 9.57 秒，总耗时 14.14 秒 |
