"""
database/seed_companies.py
Seeds ~100 top companies and their job listings.
Run automatically from app.py on first launch.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.models import get_db

COMPANIES = [
    # (name, industry, location, size, description, website, logo_icon, has_internship)
    ("Google","Technology","Bangalore / Remote","10000+","Leading search and AI company.",                     "https://careers.google.com","bi-google",1),
    ("Microsoft","Technology","Hyderabad / Remote","10000+","Cloud, AI and productivity software giant.",      "https://careers.microsoft.com","bi-microsoft",1),
    ("Amazon","Technology / E-commerce","Bangalore","10000+","World's largest e-commerce and cloud provider.", "https://amazon.jobs","bi-amazon",1),
    ("Infosys","IT Services","Pune / Bangalore","10000+","Global IT consulting and outsourcing.",              "https://infosys.com/careers","bi-building",1),
    ("TCS","IT Services","Mumbai / Pan-India","10000+","Largest Indian IT services company.",                 "https://tcs.com/careers","bi-building",1),
    ("Wipro","IT Services","Bangalore","10000+","IT, consulting and business process services.",              "https://wipro.com/careers","bi-building",1),
    ("HCL Technologies","IT Services","Noida","10000+","Global technology company.",                          "https://hcltech.com/careers","bi-building",1),
    ("Accenture","Consulting","Bangalore / Mumbai","10000+","Professional services and consulting.",          "https://accenture.com/careers","bi-briefcase",1),
    ("IBM","Technology","Bangalore / Hyderabad","10000+","AI, cloud, and enterprise solutions.",              "https://ibm.com/employment","bi-building",1),
    ("Cognizant","IT Services","Chennai / Hyderabad","10000+","Digital, technology, consulting services.",    "https://careers.cognizant.com","bi-building",1),
    ("Flipkart","E-commerce","Bangalore","5000-10000","India's leading e-commerce marketplace.",              "https://flipkartcareers.com","bi-bag-fill",1),
    ("Swiggy","Food Tech","Bangalore","5000-10000","Food delivery and quick commerce platform.",              "https://careers.swiggy.com","bi-bicycle",1),
    ("Zomato","Food Tech","Gurgaon","5000-10000","Online food delivery platform.",                            "https://zomato.com/careers","bi-bicycle",0),
    ("Paytm","Fintech","Noida","5000-10000","Digital payments and financial services.",                       "https://paytm.com/careers","bi-credit-card-fill",1),
    ("BYJU'S","EdTech","Bangalore","5000-10000","Online learning platform.",                                  "https://byjus.com/careers","bi-book-fill",1),
    ("Ola","Transport Tech","Bangalore","5000-10000","Ride-hailing and EV mobility platform.",                "https://ola.com/careers","bi-car-front-fill",1),
    ("Razorpay","Fintech","Bangalore","1000-5000","Payment gateway and financial infrastructure.",            "https://razorpay.com/jobs","bi-credit-card-fill",1),
    ("CRED","Fintech","Bangalore","1000-5000","Credit card bill payments and rewards.",                       "https://cred.club/careers","bi-gem",1),
    ("Meesho","E-commerce","Bangalore","1000-5000","Social commerce platform.",                               "https://meesho.io/careers","bi-shop",1),
    ("PhonePe","Fintech","Bangalore","1000-5000","Digital payments platform.",                                "https://phonepe.com/careers","bi-phone-fill",1),
    ("Salesforce","CRM / Cloud","Hyderabad","10000+","World's #1 CRM platform.",                             "https://salesforce.com/careers","bi-cloud-fill",1),
    ("Adobe","Software","Noida / Bangalore","10000+","Creative software and digital marketing.",              "https://adobe.com/careers","bi-palette-fill",1),
    ("Oracle","Software / Cloud","Hyderabad","10000+","Enterprise database and cloud solutions.",             "https://oracle.com/careers","bi-database-fill",1),
    ("SAP","Enterprise Software","Bangalore","10000+","ERP and enterprise software leader.",                  "https://sap.com/careers","bi-gear-fill",1),
    ("Capgemini","Consulting / IT","Mumbai / Pune","10000+","IT services and digital transformation.",        "https://capgemini.com/careers","bi-briefcase",1),
    ("Tech Mahindra","IT Services","Pune","10000+","IT solutions, digital transformation.",                   "https://techmahindra.com/careers","bi-building",1),
    ("Mphasis","IT Services","Bangalore","5000-10000","Applied technology services company.",                 "https://mphasis.com/careers","bi-building",0),
    ("Freshworks","SaaS","Chennai","1000-5000","Customer engagement software.",                               "https://freshworks.com/company/careers","bi-headset",1),
    ("Zoho","SaaS","Chennai","5000-10000","Suite of business and productivity apps.",                        "https://zoho.com/careers","bi-layout-text-window-reverse",1),
    ("MakeMyTrip","Travel Tech","Gurgaon","1000-5000","Online travel booking platform.",                     "https://makemytrip.com/careers","bi-airplane-fill",0),
    ("Naukri / Info Edge","HR Tech","Noida","1000-5000","India's top job portal.",                            "https://infoedge.in/careers","bi-person-lines-fill",0),
    ("Zerodha","Fintech","Bangalore","500-1000","India's largest stock broker.",                              "https://zerodha.com/careers","bi-graph-up-arrow",1),
    ("Groww","Fintech","Bangalore","500-1000","Investment and mutual funds platform.",                        "https://groww.in/p/careers","bi-trending-up",1),
    ("Navi","Fintech","Bangalore","500-1000","Lending and insurance platform.",                               "https://navi.com/careers","bi-shield-check",0),
    ("BrowserStack","DevTools","Mumbai","500-1000","Web and mobile testing platform.",                        "https://browserstack.com/careers","bi-browser-chrome",1),
    ("CleverTap","MarTech","Mumbai","500-1000","Customer engagement and analytics platform.",                 "https://clevertap.com/careers","bi-bar-chart-fill",0),
    ("Postman","DevTools","Bangalore","500-1000","API development and testing platform.",                     "https://postman.com/company/careers","bi-send-fill",1),
    ("HashedIn (Deloitte)","Consulting","Bangalore","500-1000","Product engineering company.",               "https://hashedin.com/careers","bi-building",0),
    ("ThoughtWorks","Consulting","Bangalore","5000-10000","Technology consulting and software.",              "https://thoughtworks.com/careers","bi-lightbulb-fill",1),
    ("Juspay","Fintech","Bangalore","500-1000","Payments infrastructure startup.",                           "https://juspay.in/careers","bi-wallet2",0),
    ("Dunzo","Quick Commerce","Bangalore","500-1000","Hyperlocal delivery platform.",                         "https://dunzo.com/careers","bi-lightning-fill",0),
    ("Lenskart","D2C / Retail","Gurgaon","1000-5000","Online eyewear brand.",                                "https://lenskart.com/careers","bi-eye-fill",0),
    ("Urban Company","Services Tech","Gurgaon","1000-5000","Home services marketplace.",                     "https://urbancompany.com/careers","bi-house-fill",0),
    ("InMobi","AdTech","Bangalore","1000-5000","Mobile advertising and marketing cloud.",                    "https://inmobi.com/company/careers","bi-phone-fill",0),
    ("Games24x7","Gaming","Mumbai","500-1000","Online gaming platform.",                                     "https://games24x7.com/careers","bi-controller",1),
    ("Dream11","Gaming / Sports","Mumbai","1000-5000","Fantasy sports platform.",                             "https://dream11.com/careers","bi-trophy-fill",1),
    ("ShareChat","Social Media","Bangalore","1000-5000","Indian social media platform.",                      "https://sharechat.com/careers","bi-chat-dots-fill",1),
    ("Lokal","Social Media","Hyderabad","100-500","Hyperlocal social network.",                               "https://lokal.app/careers","bi-globe2",0),
    ("Sprinklr","MarTech","Bangalore","1000-5000","Unified customer experience management.",                  "https://sprinklr.com/careers","bi-stars",0),
    ("Druva","Cloud / Data","Pune","500-1000","Cloud data protection platform.",                              "https://druva.com/company/careers","bi-cloud-check-fill",1),
    ("Nutanix","Cloud Infrastructure","Bangalore","5000-10000","Hyperconverged infrastructure.",              "https://nutanix.com/careers","bi-server",1),
    ("Qualcomm","Semiconductor","Hyderabad","5000-10000","Semiconductor and wireless tech.",                  "https://qualcomm.com/company/careers","bi-cpu-fill",1),
    ("Intel","Semiconductor","Bangalore","10000+","Processor and semiconductor giant.",                      "https://intel.com/content/www/us/en/jobs","bi-cpu-fill",1),
    ("AMD","Semiconductor","Hyderabad","5000-10000","Advanced processor and GPU manufacturer.",               "https://amd.com/en/corporate/careers","bi-gpu-card",1),
    ("NVIDIA","AI / GPU","Bangalore","5000-10000","AI computing and GPU leader.",                             "https://nvidia.com/en-us/about-nvidia/careers","bi-gpu-card",1),
    ("Cisco","Networking","Bangalore","10000+","Networking hardware and cybersecurity.",                      "https://cisco.com/c/en/us/about/careers","bi-hdd-network-fill",1),
    ("Palo Alto Networks","Cybersecurity","Bangalore","5000-10000","Next-gen cybersecurity platform.",         "https://paloaltonetworks.com/company/careers","bi-shield-fill",1),
    ("CrowdStrike","Cybersecurity","Bangalore","1000-5000","Cloud-native endpoint security.",                 "https://crowdstrike.com/careers","bi-shield-lock-fill",1),
    ("Zscaler","Cybersecurity","Bangalore","1000-5000","Cloud security platform.",                            "https://zscaler.com/careers","bi-lock-fill",1),
    ("PayPal","Fintech","Chennai","5000-10000","Global digital payments leader.",                             "https://paypal.com/us/webapps/mpp/jobs","bi-paypal",0),
    ("Goldman Sachs","Finance","Bangalore / Hyderabad","10000+","Global investment banking firm.",            "https://goldmansachs.com/careers","bi-bank",1),
    ("JPMorgan Chase","Finance","Bangalore","10000+","Global financial services firm.",                       "https://careers.jpmorgan.com","bi-bank",1),
    ("Morgan Stanley","Finance","Mumbai","5000-10000","Investment bank and financial services.",              "https://morganstanley.com/people/careers","bi-bank",0),
    ("Deloitte","Consulting","Pan-India","10000+","Big 4 professional services firm.",                       "https://deloitte.com/global/en/pages/careers","bi-briefcase",1),
    ("EY (Ernst & Young)","Consulting","Pan-India","10000+","Big 4 accounting and consulting.",              "https://ey.com/en_in/careers","bi-briefcase",1),
    ("PwC","Consulting","Pan-India","10000+","Big 4 accounting and advisory.",                               "https://pwc.in/careers","bi-briefcase",0),
    ("KPMG","Consulting","Pan-India","10000+","Big 4 audit, tax, and advisory.",                             "https://kpmg.com/in/en/home/careers","bi-briefcase",0),
    ("McKinsey & Company","Consulting","Gurgaon","1000-5000","Top global management consulting.",            "https://mckinsey.com/careers","bi-graph-up-arrow",1),
    ("Boston Consulting Group","Consulting","Mumbai","1000-5000","Global management consulting.",            "https://bcg.com/careers","bi-graph-up-arrow",1),
    ("Bain & Company","Consulting","Mumbai","500-1000","Management consulting firm.",                         "https://bain.com/careers","bi-graph-up-arrow",0),
    ("Myntra","Fashion Tech","Bangalore","5000-10000","India's leading fashion e-commerce.",                  "https://myntra.com/careers","bi-bag-heart-fill",1),
    ("Nykaa","Beauty Tech","Mumbai","1000-5000","Beauty and fashion e-commerce platform.",                   "https://nykaa.com/careers","bi-star-fill",0),
    ("BigBasket","Grocery Tech","Bangalore","5000-10000","Online grocery delivery platform.",                 "https://bigbasket.com/careers","bi-basket-fill",0),
    ("Blinkit (Zomato)","Quick Commerce","Gurgaon","1000-5000","10-minute grocery delivery.",                "https://blinkit.com/careers","bi-lightning-charge-fill",0),
    ("1mg (Tata)","HealthTech","Gurgaon","1000-5000","Online pharmacy and health platform.",                 "https://1mg.com/careers","bi-capsule",0),
    ("Practo","HealthTech","Bangalore","1000-5000","Digital healthcare platform.",                            "https://practo.com/careers","bi-hospital-fill",1),
    ("Apollo 24|7","HealthTech","Hyderabad","1000-5000","Digital health and pharmacy.",                      "https://apollo247.com/careers","bi-heart-pulse-fill",0),
    ("Cure.fit","HealthTech / Fitness","Bangalore","1000-5000","Fitness and wellness platform.",             "https://cure.fit/careers","bi-activity",1),
    ("Udaan","B2B Commerce","Bangalore","1000-5000","B2B trade platform for businesses.",                    "https://udaan.com/careers","bi-truck",0),
    ("Delhivery","Logistics","Gurgaon","5000-10000","Tech-driven logistics company.",                        "https://delhivery.com/careers","bi-box-seam-fill",0),
    ("Porter","Logistics Tech","Bangalore","1000-5000","Intra-city logistics platform.",                     "https://porter.in/careers","bi-truck-front-fill",0),
    ("Rivigo","Logistics","Gurgaon","1000-5000","Technology-enabled logistics company.",                     "https://rivigo.com/careers","bi-truck",0),
    ("Ather Energy","EV Tech","Bangalore","1000-5000","Electric two-wheeler manufacturer.",                  "https://atherenergy.com/careers","bi-lightning-charge-fill",1),
    ("Ola Electric","EV Tech","Bangalore","1000-5000","Electric vehicle manufacturer.",                      "https://olaelectric.com/careers","bi-ev-station-fill",1),
    ("Stellantis (Jeep/Fiat)","Automotive","Pune","5000-10000","Global automaker.",                         "https://stellantis.com/en/careers","bi-car-front-fill",0),
    ("Tata Motors","Automotive","Mumbai / Pune","10000+","India's largest automobile company.",              "https://tatamotors.com/careers","bi-car-front-fill",1),
    ("Mahindra","Automotive / Tech","Mumbai","10000+","Conglomerate with auto and tech divisions.",          "https://mahindra.com/careers","bi-building",1),
    ("L&T Technology Services","Engineering","Mysore","5000-10000","Engineering R&D services.",              "https://ltts.com/careers","bi-gear-wide-connected",1),
    ("ISRO","Space / Research","Bangalore","5000-10000","Indian space research organization.",               "https://isro.gov.in/careers","bi-rocket-takeoff-fill",1),
    ("DRDO","Defence / Research","Delhi","5000-10000","Defence research and development.",                   "https://drdo.gov.in/careers","bi-shield-fill",0),
    ("Siemens","Industrial Tech","Pune / Bangalore","5000-10000","Industrial automation and digitalization.", "https://siemens.com/global/en/company/jobs","bi-gear-fill",1),
    ("Honeywell","Industrial Tech","Hyderabad","5000-10000","Aerospace and building technologies.",          "https://honeywell.com/us/en/careers","bi-building",1),
    ("Bosch","Automotive Tech","Bangalore","5000-10000","Global automotive and industrial tech.",            "https://bosch.com/careers","bi-gear-wide-connected",1),
    ("3M","Manufacturing","Bangalore","1000-5000","Science and technology conglomerate.",                    "https://3m.com/3M/en_US/careers","bi-layers-fill",0),
    ("Unilever / HUL","FMCG","Mumbai","10000+","Consumer goods giant.",                                     "https://unilever.com/careers","bi-bag-fill",1),
    ("Procter & Gamble","FMCG","Mumbai","5000-10000","Global consumer goods company.",                      "https://us.pg.com/careers","bi-bag-fill",1),
    ("Nestle","FMCG","Gurgaon","5000-10000","Global food and beverage company.",                            "https://nestle.in/careers","bi-cup-hot-fill",0),
    ("Airtel","Telecom","Gurgaon","10000+","India's leading telecom operator.",                              "https://airtel.in/careers","bi-broadcast-pin",1),
    ("Jio (Reliance)","Telecom / Tech","Mumbai","10000+","Digital services and telecom conglomerate.",       "https://jio.com/en-in/careers","bi-wifi",1),
    ("HDFC Bank","Banking","Mumbai","10000+","India's largest private bank.",                                "https://hdfcbank.com/careers","bi-bank",1),
    ("ICICI Bank","Banking","Mumbai","10000+","India's second largest private bank.",                        "https://icicicareers.com","bi-bank",1),
    ("Axis Bank","Banking","Mumbai","10000+","Third largest private sector bank.",                           "https://axisbank.com/careers","bi-bank",0),
    ("National Instruments (NI)","Test & Measurement","Bangalore","1000-5000","Test and measurement systems.", "https://ni.com/en/about-ni/careers","bi-graph-up",0),
]

JOB_ROLES = [
    # (company_name, title, domain, location, job_type, salary_min, salary_max, skills, description, is_internship, posted_days_ago)
    ("Google","Software Engineer","Information Technology","Bangalore","Full-time",18,35,"Python,Go,System Design,DSA,Cloud","Design and build scalable software systems at Google.",0,2),
    ("Google","AI/ML Engineer","Information Technology","Bangalore / Remote","Full-time",22,40,"Python,TensorFlow,ML,Deep Learning","Develop cutting-edge ML models and AI infrastructure.",0,3),
    ("Google","Data Scientist","Analytics","Bangalore","Full-time",20,38,"Python,Statistics,SQL,BigQuery","Extract insights from massive datasets to drive decisions.",0,5),
    ("Google","SWE Intern","Information Technology","Bangalore","Internship",5,8,"Python,DSA,Problem Solving","Software engineering internship at Google.",1,1),
    ("Microsoft","Software Engineer","Information Technology","Hyderabad","Full-time",16,32,"C#,.NET,Azure,DSA","Build enterprise software and cloud services.",0,4),
    ("Microsoft","Cloud Engineer","Information Technology","Hyderabad / Remote","Full-time",18,35,"Azure,Kubernetes,DevOps,Terraform","Design and manage Azure cloud infrastructure.",0,2),
    ("Microsoft","Product Manager","Business","Hyderabad","Full-time",20,40,"Product Strategy,Agile,Data Analysis","Drive product vision and roadmap for Microsoft products.",0,7),
    ("Amazon","SDE-1","Information Technology","Bangalore","Full-time",15,28,"Java,DSA,System Design,AWS","Build highly scalable distributed systems at Amazon.",0,1),
    ("Amazon","Data Analyst","Analytics","Bangalore","Full-time",12,22,"SQL,Python,Excel,Tableau","Analyse business data and generate actionable insights.",0,3),
    ("Amazon","DevOps Engineer","Information Technology","Bangalore","Full-time",14,26,"AWS,Docker,Kubernetes,CI/CD","Manage cloud infrastructure and deployment pipelines.",0,5),
    ("Amazon","SDE Intern","Information Technology","Bangalore","Internship",4,7,"Python/Java,DSA","SDE internship at Amazon India.",1,2),
    ("Infosys","Full-Stack Developer","Information Technology","Pune","Full-time",8,16,"React,Node.js,Java,SQL","Develop full-stack enterprise web applications.",0,6),
    ("Infosys","Data Engineer","Analytics","Bangalore","Full-time",9,18,"Python,Spark,Hadoop,SQL","Build data pipelines and analytics infrastructure.",0,4),
    ("Infosys","Cybersecurity Analyst","Cybersecurity","Hyderabad","Full-time",8,15,"Network Security,SIEM,ISO 27001","Protect enterprise systems from cyber threats.",0,3),
    ("TCS","Software Developer","Information Technology","Pan-India","Full-time",7,14,"Java,Python,SQL","Develop and maintain enterprise software systems.",0,1),
    ("TCS","Business Analyst","Business","Mumbai","Full-time",8,15,"Excel,SQL,Communication,JIRA","Bridge technical teams with business stakeholders.",0,2),
    ("Wipro","Cloud Solutions Architect","Information Technology","Bangalore","Full-time",12,24,"AWS,GCP,Architecture,Terraform","Design enterprise cloud migration solutions.",0,5),
    ("Accenture","Management Consultant","Consulting","Mumbai","Full-time",12,25,"Strategy,Analytics,Communication","Advise Fortune 500 clients on business transformation.",0,3),
    ("Accenture","UI/UX Designer","Design","Bangalore","Full-time",9,18,"Figma,User Research,Prototyping","Design intuitive digital experiences.",0,4),
    ("IBM","AI Engineer","Information Technology","Bangalore","Full-time",14,28,"Python,Watson,NLP,ML","Build AI solutions using IBM Watson and open-source ML.",0,2),
    ("Flipkart","Product Manager","Business","Bangalore","Full-time",18,35,"Product Strategy,Data Analysis,Agile","Own and drive product roadmap at Flipkart.",0,3),
    ("Flipkart","Backend Engineer","Information Technology","Bangalore","Full-time",14,26,"Java,Microservices,Kafka,MySQL","Build high-performance backend services.",0,2),
    ("Swiggy","ML Engineer","Information Technology","Bangalore","Full-time",15,28,"Python,ML,Recommendation Systems","Build ML models for food delivery and logistics.",0,1),
    ("Swiggy","Android Developer","Information Technology","Bangalore","Full-time",12,22,"Android,Kotlin,Java","Build Swiggy's Android app.",0,4),
    ("Zomato","Data Scientist","Analytics","Gurgaon","Full-time",14,26,"Python,ML,Statistics,SQL","Build predictive models for Zomato's platform.",0,3),
    ("Paytm","iOS Developer","Information Technology","Noida","Full-time",11,20,"Swift,Objective-C,iOS","Build Paytm's iOS payment app.",0,5),
    ("Razorpay","Backend Engineer","Information Technology","Bangalore","Full-time",14,26,"Go,Python,MySQL,Redis","Build Razorpay's payment infrastructure.",0,2),
    ("Freshworks","Software Engineer","Information Technology","Chennai","Full-time",10,20,"Ruby on Rails,React,PostgreSQL","Build SaaS products for global customers.",0,3),
    ("Freshworks","Customer Success Engineer","Business","Chennai","Full-time",7,14,"Communication,SQL,Product Knowledge","Help customers succeed with Freshworks products.",0,4),
    ("Zoho","Full-Stack Developer","Information Technology","Chennai","Full-time",8,16,"Java,JavaScript,MySQL","Build Zoho's suite of business applications.",0,2),
    ("NVIDIA","CUDA Engineer","Information Technology","Bangalore","Full-time",20,40,"C++,CUDA,GPU Architecture,ML","Develop GPU computing frameworks and ML libraries.",0,1),
    ("NVIDIA","Deep Learning Engineer","Information Technology","Bangalore","Full-time",22,42,"Python,PyTorch,CUDA,Computer Vision","Build state-of-the-art deep learning solutions.",0,2),
    ("Intel","Hardware Engineer","Engineering","Bangalore","Full-time",14,26,"VLSI,VHDL,Circuit Design","Design and validate next-gen processor architectures.",0,3),
    ("Qualcomm","Embedded Systems Engineer","Engineering","Hyderabad","Full-time",15,28,"C,Embedded C,RTOS,Wireless","Develop firmware for Qualcomm chipsets.",0,2),
    ("Cisco","Network Engineer","Information Technology","Bangalore","Full-time",13,24,"Networking,CCNA,Python,Security","Design and manage enterprise network infrastructure.",0,3),
    ("Palo Alto Networks","Security Engineer","Cybersecurity","Bangalore","Full-time",16,30,"Python,Security,Cloud,SIEM","Build next-gen cybersecurity products.",0,2),
    ("Goldman Sachs","Quantitative Analyst","Finance","Bangalore","Full-time",22,45,"Python,Statistics,C++,Finance","Develop quantitative models for trading strategies.",0,1),
    ("Goldman Sachs","Software Engineer (Strats)","Finance","Bangalore","Full-time",20,38,"Python,C++,SQL","Build trading and risk management systems.",0,2),
    ("JPMorgan","Software Engineer","Finance","Bangalore","Full-time",16,30,"Java,Python,SQL,React","Develop financial technology platforms.",0,3),
    ("JPMorgan","Data Analyst","Analytics","Bangalore","Full-time",12,22,"SQL,Python,Tableau,Excel","Analyse financial data and generate insights.",0,4),
    ("Deloitte","Technology Consultant","Consulting","Pan-India","Full-time",11,22,"SAP,Cloud,Project Management","Deliver technology transformation projects.",0,3),
    ("Deloitte","Data & Analytics Consultant","Analytics","Bangalore","Full-time",12,24,"Python,SQL,Power BI,Statistics","Drive analytics and insights for clients.",0,2),
    ("EY","Cybersecurity Consultant","Cybersecurity","Pan-India","Full-time",10,22,"Security Auditing,ISO 27001,Penetration Testing","Assess and improve client security posture.",0,4),
    ("CRED","Backend Engineer","Information Technology","Bangalore","Full-time",16,30,"Go,Kotlin,MySQL,Redis","Build CRED's fintech platform backend.",0,2),
    ("CRED","Product Designer","Design","Bangalore","Full-time",14,26,"Figma,Product Design,UX Research","Design CRED's iconic user experience.",0,3),
    ("BrowserStack","Site Reliability Engineer","Information Technology","Mumbai","Full-time",14,26,"Kubernetes,Docker,Python,AWS","Ensure reliability of BrowserStack's testing platform.",0,2),
    ("Postman","API Engineer","Information Technology","Bangalore","Full-time",14,28,"API Design,Node.js,Go","Build Postman's API platform.",0,3),
    ("Zerodha","Quantitative Developer","Finance","Bangalore","Full-time",14,28,"Python,C++,Algorithmic Trading","Build trading systems and market analytics tools.",0,2),
    ("ThoughtWorks","Software Consultant","Consulting","Bangalore","Full-time",12,24,"Agile,TDD,Java,Microservices","Deliver consulting projects using modern engineering.",0,3),
    ("Salesforce","Platform Engineer","Information Technology","Hyderabad","Full-time",16,30,"Apex,Java,Cloud,Salesforce Platform","Develop on the Salesforce platform.",0,2),
    ("Adobe","Frontend Engineer","Information Technology","Noida","Full-time",15,28,"React,TypeScript,CSS,Performance","Build Adobe's creative cloud web applications.",0,3),
    ("SAP","ERP Consultant","Business","Bangalore","Full-time",12,24,"SAP ERP,ABAP,FI/CO","Implement SAP enterprise solutions for clients.",0,4),
    ("Myntra","Recommendation Systems Engineer","Information Technology","Bangalore","Full-time",15,28,"Python,ML,Recommendation,Spark","Build personalised fashion recommendation systems.",0,2),
    ("ShareChat","Android Developer","Information Technology","Bangalore","Full-time",12,22,"Android,Kotlin,Performance","Build ShareChat's Android app for Bharat.",0,3),
    ("Dream11","Backend Engineer","Information Technology","Mumbai","Full-time",14,26,"Java,Go,Kafka,Redis","Build real-time fantasy sports platforms.",0,2),
    ("Dream11","Data Scientist","Analytics","Mumbai","Full-time",15,28,"Python,ML,Statistics","Build predictive models for fantasy sports.",0,3),
    ("ISRO","Aerospace Engineer","Engineering","Bangalore","Full-time",8,14,"Aerospace,MATLAB,C,Orbital Mechanics","Contribute to India's space missions.",0,5),
    ("ISRO","Software Engineer (Embedded)","Engineering","Bangalore","Full-time",8,14,"Embedded C,RTOS,Python","Develop software for spacecraft and launch vehicles.",0,4),
    ("Ather Energy","Battery Systems Engineer","Engineering","Bangalore","Full-time",12,22,"Battery Technology,BMS,Python","Design next-gen EV battery systems.",0,3),
    ("Ola Electric","Embedded Software Engineer","Engineering","Bangalore","Full-time",12,22,"C,Embedded,CAN Bus,AUTOSAR","Build software for Ola's electric scooters.",0,2),
    ("Tata Motors","Mechanical Engineer","Engineering","Pune","Full-time",8,16,"AutoCAD,SolidWorks,Simulation","Design automotive components and systems.",0,3),
    ("Bosch","Automotive Systems Engineer","Engineering","Bangalore","Full-time",10,20,"CAN,Embedded C,AUTOSAR,Simulation","Develop automotive control systems.",0,2),
    ("Practo","Full-Stack Developer","Information Technology","Bangalore","Full-time",12,22,"React,Node.js,Python,PostgreSQL","Build digital healthcare solutions.",0,3),
    ("Practo","Healthcare Data Analyst","Analytics","Bangalore","Full-time",10,18,"SQL,Python,Healthcare Data","Analyse health data to improve patient outcomes.",0,4),
    ("1mg (Tata)","iOS Developer","Information Technology","Gurgaon","Full-time",11,20,"Swift,iOS,Health APIs","Build 1mg's pharmacy and health iOS app.",0,3),
    ("Udaan","Product Manager","Business","Bangalore","Full-time",16,30,"Product Strategy,B2B,Data Analysis","Drive B2B commerce product roadmap.",0,2),
    ("Delhivery","Operations Analyst","Analytics","Gurgaon","Full-time",9,16,"SQL,Excel,Logistics Analytics","Optimise last-mile delivery operations.",0,3),
    ("Airtel","Network Engineer","Engineering","Gurgaon","Full-time",10,18,"Networking,5G,RF Engineering","Design and manage Airtel's telecom network.",0,3),
    ("HDFC Bank","Data Scientist","Analytics","Mumbai","Full-time",14,24,"Python,ML,SQL,Banking","Build credit scoring and risk models.",0,2),
    ("HDFC Bank","IT Security Analyst","Cybersecurity","Mumbai","Full-time",12,22,"Security,ISO 27001,Banking Compliance","Ensure cybersecurity of banking systems.",0,3),
    ("ICICI Bank","Digital Product Manager","Business","Mumbai","Full-time",15,28,"Product,FinTech,Agile,User Research","Build ICICI's digital banking products.",0,2),
    ("Unilever / HUL","Data Analyst — Marketing","Analytics","Mumbai","Full-time",10,18,"SQL,Python,Marketing Analytics","Drive data-led marketing decisions.",0,3),
    ("McKinsey & Company","Business Analyst","Consulting","Gurgaon","Full-time",18,35,"Problem Solving,Communication,Excel","Solve complex business problems for global clients.",0,1),
    ("McKinsey & Company","Digital Analyst","Analytics","Gurgaon","Full-time",16,30,"Python,SQL,Data Science","Apply analytics in McKinsey engagements.",0,2),
    ("BCG","Consulting Analyst","Consulting","Mumbai","Full-time",18,35,"Strategy,Analytics,Presentation","Deliver strategy projects for top global firms.",0,2),
    ("Jio (Reliance)","5G Systems Engineer","Engineering","Mumbai","Full-time",12,24,"5G,Networking,Telecom Protocols","Build India's 5G network infrastructure.",0,3),
    ("Jio (Reliance)","Android Developer","Information Technology","Mumbai","Full-time",11,20,"Android,Kotlin,Jetpack","Build Jio's suite of consumer apps.",0,4),
    ("PhonePe","Risk & Fraud Analyst","Finance","Bangalore","Full-time",12,22,"Python,SQL,ML,Risk Modelling","Detect and prevent payment fraud.",0,2),
    ("Meesho","Growth Product Manager","Business","Bangalore","Full-time",15,28,"Product,Growth,SQL,A/B Testing","Drive seller and buyer growth at Meesho.",0,3),
    ("Capgemini","Java Developer","Information Technology","Pan-India","Full-time",9,18,"Java,Spring Boot,Microservices,SQL","Build enterprise Java applications.",0,2),
    ("Tech Mahindra","DevOps Engineer","Information Technology","Pune","Full-time",10,20,"Jenkins,Docker,Kubernetes,AWS","Automate software delivery pipelines.",0,3),
    ("HCL Technologies","Cybersecurity Engineer","Cybersecurity","Noida","Full-time",10,20,"Ethical Hacking,VAPT,Security Tools","Perform vulnerability assessments for clients.",0,3),
    ("Cognizant","Data Engineer","Analytics","Hyderabad","Full-time",10,20,"Python,Spark,Databricks,SQL","Build cloud data lake and ETL pipelines.",0,2),
    ("Oracle","Database Administrator","Information Technology","Hyderabad","Full-time",12,22,"Oracle DB,SQL,Performance Tuning","Manage and optimise enterprise Oracle databases.",0,3),
    ("Siemens","Automation Engineer","Engineering","Pune","Full-time",10,20,"PLC,SCADA,Industrial Automation","Design factory automation systems.",0,2),
    ("Adobe","ML Research Scientist","Information Technology","Bangalore","Full-time",22,42,"Python,Research,Computer Vision,NLP","Publish ML research and build AI features for Adobe.",0,2),
    ("BYJU'S","Content Developer","Education","Bangalore","Full-time",6,12,"Subject Knowledge,Writing,Video Production","Create engaging K-12 and competitive exam content.",0,3),
    ("BYJU'S","Software Engineer","Information Technology","Bangalore","Full-time",10,20,"React,Node.js,Python","Build EdTech platform features.",0,2),
    ("Lenskart","UI/UX Designer","Design","Gurgaon","Full-time",9,18,"Figma,User Research,E-commerce UX","Design Lenskart's shopping experience.",0,3),
    ("Urban Company","Product Manager","Business","Gurgaon","Full-time",14,26,"Product,Marketplace,Data Analysis","Build home services marketplace products.",0,2),
    ("InMobi","Mobile Ads Engineer","Information Technology","Bangalore","Full-time",14,26,"Android,iOS,Ad Tech,SDK","Build InMobi's mobile advertising SDK.",0,3),
    ("Sprinklr","Customer Experience Engineer","Business","Bangalore","Full-time",12,22,"CX Platform,SQL,Integration","Integrate Sprinklr with enterprise clients.",0,2),
    ("Druva","Cloud Security Engineer","Cybersecurity","Pune","Full-time",14,26,"AWS Security,Python,Compliance","Build cloud-native data security features.",0,2),
    ("Nutanix","Systems Software Engineer","Information Technology","Bangalore","Full-time",16,30,"C++,Distributed Systems,Python","Build Nutanix's hyperconverged infrastructure.",0,2),
    ("CrowdStrike","Security Researcher","Cybersecurity","Bangalore","Full-time",18,35,"Malware Analysis,Reverse Engineering,Python","Research and detect advanced cyber threats.",0,1),
    ("Zscaler","Cloud Architect","Information Technology","Bangalore","Full-time",18,34,"Zero Trust,Cloud Security,Networking","Design zero-trust security architectures.",0,2),
]


def seed_companies():
    conn = get_db()
    cur  = conn.cursor()

    # Companies
    company_map = {}
    for row in COMPANIES:
        cur.execute("""
            INSERT OR IGNORE INTO company
            (name,industry,location,size,description,website,logo_icon,has_internship)
            VALUES (?,?,?,?,?,?,?,?)
        """, row)
    conn.commit()

    # Build name→id map
    for row in conn.execute("SELECT company_id, name FROM company").fetchall():
        company_map[row[1]] = row[0]

    # Jobs
    for row in JOB_ROLES:
        cname = row[0]
        cid   = company_map.get(cname)
        if not cid:
            continue
        cur.execute("""
            INSERT OR IGNORE INTO job_listing
            (company_id,title,domain,location,job_type,salary_min,salary_max,
             required_skills,description,is_internship,posted_days_ago)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (cid,) + row[1:])

    conn.commit()
    conn.close()
    print(f"[SEED] Companies: {len(COMPANIES)}, Jobs: {len(JOB_ROLES)} seeded.")


if __name__ == "__main__":
    from database.models import init_db
    init_db()
    seed_companies()
