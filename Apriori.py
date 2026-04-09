import csv
import math
import itertools
from collections import defaultdict
import time

#Read csv
dataset = []

with open("Market_Basket_Optimisation.csv", newline='', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    for row in reader:
        # each row = a transaction (list of items)
        dataset.append([item.strip() for item in row if item.strip()])

#Get total # of rows
dataset_size = len(dataset)

#input min support and confidence
min_sup = float(input("Enter minimum support: "))
min_conf = float(input("Enter minimum confidence: "))
# Convert min sup to min sup count
min_sup_count = math.ceil(min_sup * dataset_size)

start_time = time.time()

# Count how many rows contain each candidate
def get_support(dataset, candidates):
    support_count = defaultdict(int)
    for row in dataset:
        #turn row into a set of items 
        row_items = set(row)
        #Loop over each candidate itemset
        for candidate in candidates:
            if set(candidate).issubset(row_items):
                #increase count if candidate appears in the row
                support_count[candidate] += 1
    # return the sup counts for all candidates            
    return support_count

# Candidate generation with join and prune steps
def generate_candidates(previous_frequent_itemsets):
    candidate_itemsets = []
    # Turn itemsets into sets 
    prev_itemsets_sets = [set(itemset) for itemset, _ in previous_frequent_itemsets]
    # Determine the size of next itemsets
    k = len(previous_frequent_itemsets[0][0]) + 1 if previous_frequent_itemsets else 1
    #Compare each pair of itemsets
    for i in range (len(prev_itemsets_sets)):
        for j in range(i +1, len(prev_itemsets_sets)):
            set1 = prev_itemsets_sets[i]
            set2 = prev_itemsets_sets[j]

            #join step. combine sets that match in all but 1 item
            set1_sorted = sorted(set1)
            set2_sorted = sorted(set2)
            if set1_sorted[:-1] == set2_sorted[:-1]:
                # merge two itemsets into a larger candidate itemset
                candidate = tuple(sorted(set1 | set2))
                #prune step. check all subsets are frequent, keep a candidate only if all its subsets are frequent
                all_subsets_frequent = all(
                    # Check if each subset exists in previous freq itemsets
                    tuple(sorted(subset)) in [item for item, _ in previous_frequent_itemsets]
                    # Generate all subsets of size k - 1 from the candidate
                    for subset in itertools.combinations(candidate, k - 1)
                )
                # if all subsets are frequent and the candidate is not already in the list
                if all_subsets_frequent and candidate not in candidate_itemsets:
                    # add the candidate to the list
                    candidate_itemsets.append(candidate)
    return candidate_itemsets

# Store all frquent itemsets found at every level
all_frequent_itemsets = []

single_item_candidates = set()

for row in dataset:
    for item in row:
        single_item_candidates.add((item,))

current_candidates = list(single_item_candidates)
total_candidate_count = 0
level_candidate_counts = []

while current_candidates:
    #Count how many candidates at this level
    num_candidates = len(current_candidates)
    total_candidate_count += num_candidates
    level_candidate_counts.append(num_candidates)

    # count how many rows contain each candidate itemset
    support_count = get_support(dataset, current_candidates)

    #filter to keep only itemsets meeting the min sup 
    current_freq_itemsets = [
        (itemset, count) for itemset, count in support_count.items() if count >= min_sup_count
    ]
    if not current_freq_itemsets:
        break
        
    all_frequent_itemsets.extend(current_freq_itemsets)

    # generate next candidate set
    current_candidates = generate_candidates(current_freq_itemsets)

end_time = time.time()
runtime = end_time - start_time

num_itemsets = len(all_frequent_itemsets)

# generate association rules
rules = []
# Convert frequent itemsets into a dict
frequent_sup_dict = {frozenset(itemset): count for itemset, count in all_frequent_itemsets}

#Loop through all frequent itemsets
for itemset, itemset_count in all_frequent_itemsets:
    #Skip itemsets with only 1 item
    if len(itemset) < 2:
        continue
    # Convert to frozenset for set operations and dict lookup
    itemset_frozen = frozenset(itemset)

   # Generate all not empty LHS subsets
    for subset_size in range(1, len(itemset)):
        for lhs in itertools.combinations(itemset, subset_size):
            lhs_frozen = frozenset(lhs)
            rhs_frozen = itemset_frozen - lhs_frozen
            #Count how many times LHS appears
            lhs_support_count = frequent_sup_dict.get(lhs_frozen, 0)
            if lhs_support_count == 0:
                continue
            #Compute confidence
            confidence = itemset_count / lhs_support_count
            # Only keep rules where the confidence meets the confidence threshold
            if confidence >= min_conf:
                lhs_str = "{" + ", ".join(lhs) + "}"
                rhs_str = "{" + ", ".join(rhs_frozen) + "}"
                # calculate support of an itemset
                itemset_support = itemset_count / dataset_size
                rules.append(
                    (lhs_str, rhs_str, round(itemset_support, 2), round(confidence, 2))
                )


# Save rules to Rules.txt
with open("RulesApriori.txt", "w") as f:
    f.write(f"Runtime: {runtime:.4f} seconds\n")
    f.write(f"Number of frequent itemsets: {num_itemsets}\n")
    f.write(f"Total candidate itemsets: {total_candidate_count}\n\n")
    

    for i, (lhs, rhs, sup, conf) in enumerate(rules, start=1):
        f.write(f"Rule#{i}: {lhs} => {rhs}\n")