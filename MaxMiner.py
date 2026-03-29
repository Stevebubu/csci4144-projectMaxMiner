# MaxMiner.py
# this is my part, implements the Max-Miner algorithm
import csv
import math
import time
from collections import defaultdict


# loading the dataset
# no header in this csv, each line is just a transaction
# stripping whitespace because some rows had extra spaces

def load_basket_data(filepath):
    basket_list = []
    with open(filepath, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            cleaned = [item.strip() for item in row if item.strip()]
            if cleaned:
                basket_list.append(cleaned)
    return basket_list


# get every unique item in the dataset

def get_all_items(basket_list):
    all_items = set()
    for transaction in basket_list:
        all_items.update(transaction)
    return sorted(all_items)


# check if an itemset meets the support threshold

def is_frequent(itemset, basket_list, min_sup_count):
    count = sum(1 for t in basket_list if itemset.issubset(set(t)))
    return count >= min_sup_count


def get_support_count(itemset, basket_list):
    return sum(1 for t in basket_list if itemset.issubset(set(t)))


def is_subset_of_any_maximal(candidate, maximal_itemsets):
    # if we already have a bigger set that covers this one, skip it
    return any(candidate.issubset(mx) for mx in maximal_itemsets)


# MAX-MINER
# each node in the search is a (head, tail) pair
#   head = items we've committed to
#   tail = items we could still add
# if head+tail is frequent we keep extending
# if not, we trim the tail to only items that actually work with head
# this way we skip a ton of candidates that apriori would have checked

def run_max_miner(basket_list, min_sup_count):
    all_items = get_all_items(basket_list)
    maximal_itemsets = []

    # one starting node per item, tail is everything after it alphabetically
    # doing it this way avoids checking the same combo twice
    initial_nodes = []
    for i, item in enumerate(all_items):
        head = frozenset([item])
        tail = frozenset(all_items[i + 1:])
        initial_nodes.append((head, tail))

    queue = initial_nodes

    while queue:
        next_queue = []

        for head, tail in queue:
            full_set = head | tail

            if not tail:
                # nothing left to add, head is as big as it gets
                if is_frequent(head, basket_list, min_sup_count):
                    if not is_subset_of_any_maximal(head, maximal_itemsets):
                        maximal_itemsets.append(head)
                continue

            full_frequent = is_frequent(full_set, basket_list, min_sup_count)

            if full_frequent:
                # whole thing is frequent, record it and keep extending head
                if not is_subset_of_any_maximal(full_set, maximal_itemsets):
                    maximal_itemsets.append(full_set)
                tail_list = sorted(tail)
                for i, item in enumerate(tail_list):
                    new_head = head | frozenset([item])
                    new_tail = frozenset(tail_list[i + 1:])
                    next_queue.append((new_head, new_tail))
            else:
                # head+tail isn't frequent so trim tail to only items that work with head
                surviving_tail = frozenset(
                    item for item in tail
                    if is_frequent(head | frozenset([item]), basket_list, min_sup_count)
                )
                if is_frequent(head, basket_list, min_sup_count):
                    # head is frequent and can't be extended fully so it's maximal
                    if not is_subset_of_any_maximal(head, maximal_itemsets):
                        maximal_itemsets.append(head)

                if surviving_tail:
                    tail_list = sorted(surviving_tail)
                    for i, item in enumerate(tail_list):
                        new_head = head | frozenset([item])
                        new_tail = frozenset(tail_list[i + 1:])
                        next_queue.append((new_head, new_tail))

        queue = next_queue
    # remove anything that ended up being a subset of a bigger maximal set
    cleaned = []
    for mx in maximal_itemsets:
        if not any(mx < other for other in maximal_itemsets):
            cleaned.append(mx)

    return cleaned


# writing results to file
def itemset_to_str(frozen):
    return "{" + ", ".join(sorted(frozen)) + "}"


def write_results(max_miner_itemsets, basket_list, total_records,
                  min_sup, min_sup_count, maxminer_time, output_path):

    with open(output_path, "w") as f:
        f.write("Max-Miner Results\n")
        f.write("Group: Charlie Livingstone, Tung Vu, Efe Ivagba\n")
        f.write("Dataset: Market_Basket_Optimisation.csv\n")
        f.write(f"Total transactions: {total_records}\n")
        f.write(f"min_sup: {min_sup} (count = {min_sup_count})\n")
        f.write(f"Time taken: {maxminer_time:.4f} seconds\n")
        f.write(f"Maximal frequent itemsets found: {len(max_miner_itemsets)}\n\n")

        for i, itemset in enumerate(sorted(max_miner_itemsets, key=lambda x: -len(x)), 1):
            cnt = get_support_count(itemset, basket_list)
            sup = round(cnt / total_records, 2)
            f.write(f"Maximal#{i}: {itemset_to_str(itemset)} - support: {sup}\n")


# main
def main():
    dataset_filepath = "Market_Basket_Optimisation.csv"
    output_path = "MaxMiner_Results.txt"

    print("\nMax-Miner Algorithm")
    print("Efe Ivagba - B00909028\n")

    while True:
        try:
            min_sup_input = float(input("enter min_sup (e.g. 0.05): ").strip())
            if not (0 < min_sup_input <= 1):
                print("has to be between 0 and 1, try again")
                continue
            break
        except ValueError:
            print("enter a decimal like 0.05")

    print(f"\nloading {dataset_filepath} ...")
    basket_list = load_basket_data(dataset_filepath)
    total_records = len(basket_list)
    print(f"transactions loaded: {total_records}")

    min_sup_count = math.ceil(min_sup_input * total_records)
    print(f"min_sup count: ceil({min_sup_input} x {total_records}) = {min_sup_count}")

    print("\nrunning Max-Miner ...")
    t0 = time.time()
    maxminer_result = run_max_miner(basket_list, min_sup_count)
    maxminer_time = time.time() - t0
    print(f"done - {len(maxminer_result)} maximal itemsets found in {maxminer_time:.4f}s")

    write_results(maxminer_result, basket_list, total_records,
                  min_sup_input, min_sup_count, maxminer_time, output_path)

    print(f"\nresults saved to {output_path}\n")


if __name__ == "__main__":
    main()