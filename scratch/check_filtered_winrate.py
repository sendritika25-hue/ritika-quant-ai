import pandas as pd

log_path = "/home/sendritika25/trading_ai/prediction_log.csv"
df = pd.read_csv(log_path)
val = df[df['Status'] == 'VALIDATED'].copy()

val['Conf_Num'] = val['Confidence'].astype(str).str.replace('%', '').astype(float)
high_conf = val[val['Conf_Num'] >= 60.0].copy()

correct_hc = high_conf[high_conf['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)]

print("=== HIGH CONFIDENCE (>=60% CONFIDENCE) AUDIT RESULT ===")
print(f"Total High-Confidence Trades Logged: {len(high_conf)}")
print(f"Correct High-Confidence Trades: {len(correct_hc)}")
if len(high_conf) > 0:
    hc_win_rate = (len(correct_hc) / len(high_conf)) * 100
    print(f"🔥 High-Confidence AI Win-Rate: {hc_win_rate:.2f}%")

# Break down Intraday vs Delivery High-Confidence
hc_intra = high_conf[high_conf['Ticker'].astype(str).str.contains('\(Intraday\)', case=False, na=False)]
hc_intra_correct = hc_intra[hc_intra['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)]

hc_deliv = high_conf[~high_conf['Ticker'].astype(str).str.contains('\(Intraday\)|\(LongTerm\)', case=False, na=False)]
hc_deliv_correct = hc_deliv[hc_deliv['Outcome'].astype(str).str.contains('CORRECT', case=False, na=False)]

print("\n--- MODE BREAKDOWN (HIGH CONFIDENCE) ---")
if len(hc_intra) > 0:
    print(f"⚡ Intraday High-Conf Win-Rate: {(len(hc_intra_correct)/len(hc_intra))*100:.2f}% ({len(hc_intra_correct)}/{len(hc_intra)})")
if len(hc_deliv) > 0:
    print(f"🏆 Delivery High-Conf Win-Rate: {(len(hc_deliv_correct)/len(hc_deliv))*100:.2f}% ({len(hc_deliv_correct)}/{len(hc_deliv)})")

