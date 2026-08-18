#!/bin/sh
VACANCY_NAME="${1:-Python developer}"

VACANCY_NAME=$(echo "$VACANCY_NAME" | sed 's/ /%20/g')

curl -s -H "User-Agent: Mozilla/5.0" \
"https://api.hh.ru/vacancies?text=${VACANCY_NAME}&area=2759&per_page=20" \
| jq '.' > hh.json
