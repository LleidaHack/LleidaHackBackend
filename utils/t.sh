counter=0
for i in {1..100}
do
  response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://backend.integration.lleidahack.dev/mail_queue/send_mail" -H "accept: application/json" -H "Authorization: Bearer HOLA")
  if [ $response -ne 200 ]
  then
    echo "Response Code: $response"
    echo "Executed $counter times before failure."
    exit 1
  fi
  counter=$((counter+1))
done

