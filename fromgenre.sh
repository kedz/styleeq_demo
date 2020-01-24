SENT1="That even the powers of time can be altered for a single purpose?"
SENT2="Nothing is so painful to the human mind as a great and sudden change."



### Generate from source sentences and genre ###

SOURCES="[\"$SENT1\", \"$SENT2\"]"
#GENRE="\"scifi\""
#GENRE="\"philosophy\""
GENRE="\"gothic\""

# 1. Get pivot features for gothic corpus, num_pivots determines the number
#    of pivots to retrieve. sources is a list of sentences to get pivots for. 
#    Returns {"sources": [list of source strings], 
#             "features": [list of features for each source sentence],
#             "pivots": [list of lists of num_pivot pivot features]}

POSTDATA="{\"sources\": $SOURCES, \"genre\": $GENRE, \"num_pivots\": 2}"
PIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$POSTDATA" \
    http://localhost:5000/styleeq/api/v1.0/getpivots)

echo "### PIVOT FEATURES ###"
echo "$PIVOTS"

# 2. Generate from source content and pivot features.
#    Returns {"output": [
#                        {
#                            "source": source sent, 
#                            "transfers": [
#                                {
#                                    "pivot": pivot sentence, 
#                                    "transfer": transfered sentence
#                                },...
#                             ]
#                          }, 
#                          ...
#                         ]}

                        

FROMPIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$PIVOTS" \
    http://localhost:5000/styleeq/api/v1.0/frompivots)
echo "### GENERATION FROM PIVOTS ###"
echo "$FROMPIVOTS"


