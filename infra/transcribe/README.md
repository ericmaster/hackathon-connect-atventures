# Transcribe custom vocab `connect-atv-meds` (es-US, us-east-1)

What: 69 med/brand terms (Buprex, Tempra, Apronax, SmartClub, Medicity…). Public/synthetic names only.
File: `connect-atv-meds.tsv` = AWS table (Phrase/SoundsLike/IPA/DisplayAs, TAB). SoundsLike+IPA ignored by AWS now → empty.
Rule: Phrase no spaces, no digits, hyphen = multiword. Phonetic hints = extra Phrase row + DisplayAs canonical (e.g. `A-Pronax` → `Apronax`).
Edit `build_table.py`, not tsv. More variants ≠ better (v2/v4 regressed); always A/B.

Build + upload + create/update:
```
cd infra/transcribe && python build_table.py
aws s3 cp connect-atv-meds.tsv s3://connect-atv-gliner-build-325556500173/transcribe/connect-atv-meds.txt   # private bucket
aws transcribe create-vocabulary --region us-east-1 --vocabulary-name connect-atv-meds --language-code es-US \
  --vocabulary-file-uri s3://connect-atv-gliner-build-325556500173/transcribe/connect-atv-meds.txt
#   (exists? same args with update-vocabulary)
aws transcribe get-vocabulary --region us-east-1 --vocabulary-name connect-atv-meds --query '[VocabularyState,FailureReason]'
```
PENDING ~2 min → READY.

Use: Lambda env `FV_TRANSCRIBE_VOCABULARY=connect-atv-meds` (voice.handle_stt_url adds it to presigned URL).
A/B local, no Lambda: `[FV_TRANSCRIBE_VOCABULARY=connect-atv-meds] /workspace/.venv-c/bin/python infra/transcribe/ab_test.py`
Teardown: `aws transcribe delete-vocabulary --region us-east-1 --vocabulary-name connect-atv-meds`
