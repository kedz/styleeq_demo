SENT1="That even the powers of time can be altered for a single purpose?"
SENT2="Nothing is so painful to the human mind as a great and sudden change."

FEATS=$(curl -s -H "Content-Type: application/json" -X POST \
    -d "{\"sources\": [\"$SENT1\", \"$SENT2\"]}" \
    http://localhost:5000/styleeq/api/v1.0/getfeatures)

# 2. Generate from  features
FROMFEATS=$(curl -s -H "Content-Type: application/json" -X POST -d "$FEATS" \
    http://localhost:5000/styleeq/api/v1.0/fromfeatures)

echo "### GENERATION FROM FEATURES ###"
echo "$FROMFEATS"




