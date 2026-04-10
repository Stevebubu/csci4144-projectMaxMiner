import java.io.*;
import java.util.*;

class Transaction {
    List<String> items;

    public Transaction(List<String> items) {
        this.items = items;
    }
}


public class MaxMiner {

    static List<Transaction> transactions = new ArrayList<>();
    static int min_sup_count;
    static double min_conf;

    static Map<Set<String>, Integer> maximalItemsets = new LinkedHashMap<>();

    public static void main(String[] args) throws IOException {

        // LOAD DATASET
        File dataset = new File("Market_Basket_Optimisation.csv");
        BufferedReader br = new BufferedReader(new FileReader(dataset));
        String line;

        while ((line = br.readLine()) != null) {
            String[] parts = line.split(",");
            List<String> items = new ArrayList<>();

            for (String item : parts) {
                item = item.trim();
                if (!item.isEmpty())
                    items.add(item);
            }

            if (!items.isEmpty())
                transactions.add(new Transaction(items));
        }
        br.close();

        Scanner kb = new Scanner(System.in);

        System.out.print("Enter minimum support: ");
        double minSupFraction = kb.nextDouble();

        System.out.print("Enter minimum confidence: ");
        min_conf = kb.nextDouble();

        min_sup_count = (int) Math.ceil(minSupFraction * transactions.size());

        Map<String, Integer> supportCache = new HashMap<>();
        for (String item : getAllItems()) {
            int sup = getSupport(Collections.singleton(item));
            if (sup >= min_sup_count)
                supportCache.put(item, sup);
        }

        List<String> allItems = new ArrayList<>(supportCache.keySet());

        allItems.sort(Comparator.comparingInt(supportCache::get));

        //Track runtime
        long startTime = System.nanoTime();

        maxMiner(new HashSet<>(), allItems);
        
        removeNonMaximal();

        long endTime = System.nanoTime();
        double runtimeSeconds = (endTime - startTime) / 1e9;

        writeRules(minSupFraction, min_conf, runtimeSeconds);

        System.out.println("Rules written to MaxMiner_Rules.txt");
    }

    public static List<String> getAllItems() {
        Set<String> items = new HashSet<>();
        for (Transaction t : transactions)
            items.addAll(t.items);
        return new ArrayList<>(items);
    }

    public static int getSupport(Set<String> itemset) { 

        int count = 0;
        for (Transaction t : transactions) {
            if (t.items.containsAll(itemset))
                count++;
        }
        return count;
    }

    // MAX-MINER Implementation based on Bayardo (1998) Figures 2–4
    // prefix = h(g)  (the head of the current candidate group)
    // tail   = t(g)  (ordered list of remaining items that may extend the head)
    public static void maxMiner(Set<String> prefix, List<String> tail) {

        // Superset-frequency pruning (Figure 2 / Figure 4)
        // If h ∪ t is frequent, every sub-node would produce a non-maximal itemset,
        // so record h ∪ t as a maximal candidate and stop expanding.
        Set<String> combined = new HashSet<>(prefix);
        combined.addAll(tail);

        if (!combined.isEmpty() && getSupport(combined) >= min_sup_count) {
            maximalItemsets.put(new HashSet<>(combined), getSupport(combined));
            return;
        }

        // Subset-infrequency pruning + tail building (Figure 4: GEN-SUB-NODES)
        // Prune tail items whose addition to the head makes the head infrequent,
        // then generate one sub-node per remaining tail item.
        for (int i = 0; i < tail.size(); i++) {

            String item = tail.get(i);

            Set<String> newPrefix = new HashSet<>(prefix);
            newPrefix.add(item);

            // Subset-infrequency pruning: skip item if h ∪ {item} is infrequent
            if (getSupport(newPrefix) < min_sup_count)
                continue;

            // Build the new tail: items after position i that are still potentially useful.
            // Per GEN-SUB-NODES we also prune tail items j where h' ∪ {j} is infrequent.
            List<String> newTail = new ArrayList<>();
            for (int j = i + 1; j < tail.size(); j++) {
                String tailItem = tail.get(j);
                Set<String> test = new HashSet<>(newPrefix);
                test.add(tailItem);
                if (getSupport(test) >= min_sup_count)
                    newTail.add(tailItem);
            }

            maxMiner(newPrefix, newTail);
        }

        // If prefix itself is frequent and nothing extended it, it may be maximal.
        // Record it here, the removeNonMaximal pass will clean up duplicates.
        if (!prefix.isEmpty() && getSupport(prefix) >= min_sup_count) {
            maximalItemsets.putIfAbsent(new HashSet<>(prefix), getSupport(prefix));
        }
    }

    // REMOVE NON-MAXIMAL
    // After the search, ensure every stored itemset has no proper frequent superset
    // also stored (per the "remove from F" step in Figure 2).
    public static void removeNonMaximal() {
        List<Set<String>> all = new ArrayList<>(maximalItemsets.keySet());
        Set<Set<String>> toRemove = new HashSet<>();

        for (int i = 0; i < all.size(); i++) {
            if (toRemove.contains(all.get(i))) continue;
            for (int j = 0; j < all.size(); j++) {
                if (i == j || toRemove.contains(all.get(j))) continue;
                // If all.get(j) is a proper superset of all.get(i), then all.get(i) is not maximal
                if (all.get(j).containsAll(all.get(i)) && all.get(j).size() > all.get(i).size()) {
                    toRemove.add(all.get(i));
                    break;
                }
            }
        }

        for (Set<String> s : toRemove)
            maximalItemsets.remove(s);
    }

    public static List<Set<String>> getSubsets(Set<String> set) {
        List<Set<String>> subsets = new ArrayList<>();
        List<String> list = new ArrayList<>(set);
        int n = list.size();
        int total = 1 << n;

        for (int i = 1; i < total - 1; i++) {
            Set<String> subset = new HashSet<>();
            for (int j = 0; j < n; j++) {
                if ((i & (1 << j)) > 0)
                    subset.add(list.get(j));
            }
            subsets.add(subset);
        }

        return subsets;
    }

    public static void writeRules(double minSupFraction, double minConf, double runtimeSeconds) throws IOException {

        PrintWriter pw = new PrintWriter(new FileWriter("MaxMiner_Rules.txt"));

        int totalTransactions = transactions.size();
        int ruleNum = 1;

        pw.println("1. User Input:");
        pw.println();
        pw.println("Support=" + minSupFraction);
        pw.println("Confidence=" + minConf);
        pw.println();
        pw.println("2. Maximal Frequent Itemsets Found: " + maximalItemsets.size());
        pw.println();
        pw.println("Runtime: " + runtimeSeconds + " seconds");
        System.out.println("Dataset: Market_Basket_Optimisation.csv");
        pw.println();
        pw.println("3. Rules:");
        pw.println();
        

        for (Set<String> itemset : maximalItemsets.keySet()) {

            if (itemset.size() < 2)
                continue;

            int itemsetSupport = maximalItemsets.get(itemset);

            List<Set<String>> subsets = getSubsets(itemset);

            for (Set<String> antecedent : subsets) {

                Set<String> consequent = new HashSet<>(itemset);
                consequent.removeAll(antecedent);

                if (consequent.isEmpty())
                    continue;

                int antecedentSupport = getSupport(antecedent);

                if (antecedentSupport == 0)
                    continue;

                double confidence = (double) itemsetSupport / antecedentSupport;
                double support = (double) itemsetSupport / totalTransactions;

                if (confidence >= minConf) {
                    pw.println("Rule#" + ruleNum + ": " + formatSet(antecedent) + " => " + formatSet(consequent));
                    pw.println("(Support=" + round(support) + ", Confidence=" + round(confidence) + ")");
                    pw.println();
                    ruleNum++;
                }
            }
        }

        pw.println("Total rules generated: " + (ruleNum - 1));
        pw.close();
    }

    public static String formatSet(Set<String> s) {
        StringBuilder sb = new StringBuilder("{");
        Iterator<String> it = s.iterator();
        while (it.hasNext()) {
            sb.append(it.next());
            if (it.hasNext()) sb.append(", ");
        }
        sb.append("}");
        return sb.toString();
    }

    public static double round(double value) {
        return Math.round(value * 100.0) / 100.0;
    }
}