/**
 * Pure frontend statistics — no backend required.
 */

const ONE_HOUR_MS = 60 * 60 * 1000;

export function countHighRisk(transactions, threshold = 80) {
  return transactions.filter((t) => t.risk_score >= threshold).length;
}

export function countLocationMismatches(transactions) {
  return transactions.filter((t) => t.location_consistency === 0).length;
}

/**
 * Unique users with >= minCount transactions within any 1-hour sliding window.
 */
export function countHighFrequencyAccounts(transactions, minCount = 3) {
  const byUser = {};
  for (const t of transactions) {
    const uid = t.user_id;
    if (!byUser[uid]) byUser[uid] = [];
    byUser[uid].push(new Date(t.timestamp).getTime());
  }

  let accountCount = 0;
  for (const times of Object.values(byUser)) {
    times.sort((a, b) => a - b);
    let found = false;
    for (let i = 0; i < times.length && !found; i++) {
      let j = i;
      while (j < times.length && times[j] - times[i] <= ONE_HOUR_MS) j++;
      if (j - i >= minCount) {
        found = true;
        accountCount++;
      }
    }
  }
  return accountCount;
}

export function computeAllStats(transactions) {
  return {
    highRisk: countHighRisk(transactions),
    highFrequencyAccounts: countHighFrequencyAccounts(transactions),
    locationMismatches: countLocationMismatches(transactions),
  };
}
