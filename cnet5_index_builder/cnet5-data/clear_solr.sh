#!/bin/sh
# http://wiki.apache.org/solr/FAQ#How_can_I_delete_all_documents_from_my_index.3F
# http://wiki.apache.org/solr/UpdateXmlMessages#Updating_a_Data_Record_via_curl
 
 #curl "http://burgundy.media.mit.edu:8983/solr/select?q=*:*"

 curl "http://salmon.media.mit.edu:8983/solr/update?commit=true" -H "Content-Type: text/xml" --data-binary  '<delete><query>*:*</query></delete>'
