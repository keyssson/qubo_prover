"""验证 Modus Tollens 逻辑"""

print('Modus Tollens 验证')
print('=' * 60)
print('公理 1: P->Q')
print('公理 2: ~Q')
print('目标: ~P')
print()

# 测试所有可能的赋值
print('真值表验证:')
print('-' * 60)
print('P | Q | P->Q | ~Q | ~P | 满足公理? | 满足目标?')
print('-' * 60)

for P in [0, 1]:
    for Q in [0, 1]:
        # 计算公式值
        imp_pq = 1 if (P == 0 or Q == 1) else 0  # P->Q ≡ ~P ∨ Q
        not_q = 1 - Q
        not_p = 1 - P
        
        # 检查是否满足公理
        axioms_satisfied = (imp_pq == 1) and (not_q == 1)
        goal_satisfied = (not_p == 1)
        
        check_axiom = "✓" if axioms_satisfied else "✗"
        check_goal = "✓" if goal_satisfied else "✗"
        
        print(f'{P} | {Q} | {imp_pq:4d} | {not_q:2d} | {not_p:2d} | {check_axiom:^10s} | {check_goal:^10s}')

print('-' * 60)
print()
print('结论:')
print('只有 P=0, Q=0 同时满足所有公理和目标')
print('即: P=False, Q=False, ~P=True')
print('因此 Modus Tollens 推理是正确的！')

