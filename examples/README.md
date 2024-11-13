**To produce [an example event](examples/event.json), run:**
   ```bash
   docker compose -f examples/docker-compose.yml up -d --build
   ```
  
  View the streamed data on the [dashboard](http://localhost:8502/Camera_Traps). 
  
  Go to the [local neo4j instance](http://localhost:7474/browser/) with username `neo4j` and password `PWD_HERE`.
  Run ```MATCH (n) RETURN n``` to view the streamed data. 
