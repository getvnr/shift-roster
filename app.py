import random

def generate_shift_roster(employees, night_exempt, num_days, group_map=None):
    """
    Generate shift plan for employees with:
      - 5-10 days per shift type (F/S/N)
      - 2 Offs after each block
      - No Night shift for exempt employees
      - Equalized off count across all
    """
    shifts = ['F', 'S', 'N']
    roster = {emp: [''] * num_days for emp in employees}
    
    # Step 1: Generate base shift rotation
    for emp in employees:
        day = 0
        prev_shift = None
        emp_shifts = shifts.copy()
        
        if emp in night_exempt:
            emp_shifts = ['F', 'S']  # No Night shift

        while day < num_days:
            # pick next shift (not same as previous)
            possible = [s for s in emp_shifts if s != prev_shift]
            shift = random.choice(possible)
            block_len = random.randint(5, 10)
            
            # fill shift block
            for _ in range(block_len):
                if day >= num_days:
                    break
                roster[emp][day] = shift
                day += 1

            # add 2 off days
            for _ in range(2):
                if day >= num_days:
                    break
                roster[emp][day] = 'O'
                day += 1
            
            prev_shift = shift

    # Step 2: Equalize off days (so everyone has same number of O)
    off_counts = [roster[e].count('O') for e in employees]
    target_offs = round(sum(off_counts) / len(off_counts))

    for emp in employees:
        current_offs = roster[emp].count('O')
        if current_offs > target_offs:
            # Replace extra offs with previous shift
            for i, v in enumerate(roster[emp]):
                if v == 'O' and current_offs > target_offs:
                    # assign previous day's shift if available
                    prev = roster[emp][i-1] if i > 0 else 'F'
                    roster[emp][i] = prev
                    current_offs -= 1
        elif current_offs < target_offs:
            # Add offs in random working days
            work_indices = [i for i, v in enumerate(roster[emp]) if v not in ['O']]
            random.shuffle(work_indices)
            for i in work_indices:
                if current_offs >= target_offs:
                    break
                roster[emp][i] = 'O'
                current_offs += 1

    return roster
