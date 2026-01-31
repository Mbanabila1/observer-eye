plan to build observer-eye observability platform :
1. its 3 layer architecture :
   1. presentation layer 
   2. logic layer 
   3. data layer 


2. deep dive technology stack for 3 layer with security best practices

3. under this architecture:
   1. presentation layer angular 21  port 80
   2. logic layer  middleware fastapi  port 8400 
   3. data layer backend django 
   4. no mock data , no seed data , no sample data 

   
4. each layer : 
   1. presentation layer:
        0. auth -sign in, sign out,log in, log out, web identity github,gitlab,google,microsoft
           1. password management:
                1. lowercase
                2. uppercase
                3. numbers
                4. specials character
                5. password length : 16 
                6. password strength:
                    1. high
                    2. medium
                    3. low
        2. components + expand
        3. UI  + expand 
        4. services + expand 
        5. pages and sub pages + expand
        5. dashboard + expand 
        6. features + expand 
        7. integrate to middleware
   
   2. logic layer: 
      under middleware:
       1. performance + expand
       2. error_handling  + expand
       3. caching + expand
       4. testing + expand
       5. streaming + expand
       6. telemetry + expand
       7. data transformation,filtering,validation,normalization,sanization,modulerity,comprehension , poliymorphic to be clean data + expand 
       8. enable crud operation + expand
       9. ensure integrate to backend
    

    3. data layer:
     
     under backend apps /observer : 
       1. analytics + bi analyze + expand 
       2. analytics_performance_monitoring + expand
       3. application_performance_monitoring + expand
       4. appmetrics + expand
       5. core + expand
       6. grailobserver + expand 
       7. identity_performance_monitoring + expand 
       8. integration + expand 
       9. netmetrics + expand 
       10. notification + expand 
       11. security_performance_monitoring + expand 
       12. securitymetrics + expand 
       13. settings + expand
       14. template_dashboards + expand 
       15. traffic_performance_monitoring + expand 

5. dependency:
    
    internet to dashboard to middleware to backend

6. dockers:
   0. improve runtime build within 5min + security best practices
   1. create dockerfile for backend 
   2. create dockerfile for middleware 
   3. create dockerfile for dashboard
   4. create docker-compose.yml


7. docs observer-eye observability platform :
   
   1. overview.md
   2. description.md 
   3. objectives.md
   4. architecture.md 
   5. whats it solves for business and enterprise
   6. technical and feature with their capabilites 
   7. support cross platform for linux,mac,widnows