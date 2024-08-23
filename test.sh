#!/bin/bash
read -p "Username: " username
read -s -p "Password: " password
echo

url="https://rag.arianott.com"

performing_test() {
    # Replace spaces with underscores for the output filename
    filename=$(echo "$1" | tr ' ' '_')
    echo "Test: $1"

    # Record start time
    start_time=$(date +%s%3N)

    # Execute the curl command
    curl "$url/$2" -u $username:$password -s > "${filename}.txt"

    # Record end time
    end_time=$(date +%s%3N)

    # Calculate the duration
    duration=$((end_time - start_time))

    echo "Response saved to ${filename}.txt"
    echo "Time taken: ${duration}ms"
    echo
}

performing_post_test() {
    # Replace spaces with underscores for the output filename
    filename=$(echo "$1" | tr ' ' '_')
    echo "Test: $1"

    # Record start time
    start_time=$(date +%s%3N)

    # Execute the curl command
    curl -X POST "$url/$2" -u $username:$password -H "Content-Type: application/json" -d "$3" -s > "${filename}.txt"

    # Record end time
    end_time=$(date +%s%3N)

    # Calculate the duration
    duration=$((end_time - start_time))

    echo "Response saved to ${filename}.txt"
    echo "Time taken: ${duration}ms"
    echo
}

echo "Testing user:"

# Test /chat/hello
performing_test "Hello_User" "chat/hello?name=$username"

# Test /chat/xkcd
performing_test "XKCD_Meme" "chat/xkcd"

# Test /files/upload_pdf (assuming you have a sample.pdf file to upload)
# This requires a file, so only execute if you have one.
# Uncomment the below line if you want to include this test.
# curl -X POST "$url/files/upload_pdf" -u $username:$password -F "file=@sample.pdf" -s > "Upload_PDF_Response.txt"
# echo "Upload PDF response saved to Upload_PDF_Response.txt"

# Test /files/list_files
performing_test "List_Files" "files/list_files"

# Test /files/get_file/{file_id}
# You need to replace {file_id} with a valid file ID
# Uncomment the below line if you have a valid file ID
performing_test "Get_File" "files/get_file/Das-Rheingold.pdf-2024-08-19-16-33-30"

# Test /files/delete_file/{file_id}
# You need to replace {file_id} with a valid file ID
# Uncomment the below line if you have a valid file ID
# performing_test "Delete_File" "files/delete_file/{file_id}"

# Test /db/add_user (Create User)
# Replace the following JSON payload with appropriate user data.
# Uncomment the below line if you want to include this test.
# curl -X PUT "$url/db/add_user" -u $username:$password -H "Content-Type: application/json" -d '{"username": "newuser", "password": "newpass", "authorisation": "user"}' -s > "Create_User_Response.txt"
# echo "Create User response saved to Create_User_Response.txt"
#performing_test "Delete_Qdrant" "rag/delete-index"
performing_test "Create_Qdrant" "rag/create-index"
# Test /rag/update-index
#performing_test "Index_All_Files" "rag/update-index"

# Test /rag/check-background
performing_test "Check_Background_Task" "rag/check-background"





# Replace with appropriate JSON payload


performing_post_test "Naive_RAG" "rag/naive-rag/" '{
  "prompt": "Who is Siglinde?",
  "top_k": 5,
  "language": "German"
}'

# Test /rag/advanced-rag
# Replace with appropriate JSON payload
performing_post_test "Advanced_RAG" "rag/advanced-rag" '{
  "prompt": "Wer ist Kraner?",
  "top_k": 5,
  "language": "English"
}'
# Test /rag/modular-rag
# Replace with appropriate JSON payload
performing_post_test "Modular_RAG" "rag/modular-rag" '{
  "prompt": "Fasse die Praxisarbeit von Arian Ott in eigenen Worten zusammen.",
  "top_k": 5,
  "language": "German"
}'

exit 0
