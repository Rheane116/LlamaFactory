
DATASET_2_FORMAT = {
  "dfs":'''
    # 2. Input: Text to be extracted (string).
    # 3. Output: Entity and relation extraction results (string) in a specially designed serialized format.Note that the letter case in entity mentions must strictly match the original text. Do not mistakenly write uppercase letters as lowercase, or lowercase letters as uppercase!
      ## 3.1 Serialized Output Instructions: Ensure the brackets in the output sequence are properly closed and the format meets the requirements!
      (1) Graph Traversal Logic: Use the DFS graph traversal method. Entities correspond to nodes in the graph (nodes are named with entity mentions), and relations correspond to directed edges in the graph (from head entities to tail entities; directed edges are named with relation types).
      (2) Overall Structure: Formally adopt bracket nesting (square brackets []), use colons : to indicate types, and separate different nodes or edges with a single space. If an entity consists of multiple tokens, connect every two tokens with an underscore _.
      (3) Sorting Priority: The order of node expansion strictly follows the first occurrence order of corresponding entities in the text.
      (4) Handling of Repeatedly Visited Nodes: If an already expanded node is visited during node expansion, use "REF" to represent it without further expansion.
      (5) Top-level Node Deduplication: If an entity has been visited and defined in a previous DFS path, it is strictly prohibited to appear again as an independent element of the top-level list (i.e., the top-level list does not output refs for any visited nodes).
      (6) Empty Result Handling: If the entity extraction result is empty, output only the root node [ROOT].  
    ''',

  "naive":'''
    # 2. Input: Text to be extracted (string).
    # 3. Output: Entity and relation extraction results in JSON format.
      ## 3.1 Serialized Output Instructions: Ensure the output conforms to standard JSON syntax, with properly closed brackets, complete fields, and correct formatting! Note that the letter case in entity mentions must strictly match the original text. Do not mistakenly write uppercase letters as lowercase, or lowercase letters as uppercase!
        (1) Field Description: The output dictionary contains the entities field and the relations field, corresponding to entity and relation extraction results respectively.
        The entities field is a dictionary where keys are entity mentions, and values are dictionaries with a key type whose value is the entity type.
        The relations field is a list, where each element is a triple (list) corresponding to the head entity mention, relation type, and tail entity mention in order.
        (2) Empty Result Handling: If the entity set is empty, the value corresponding to entities is an empty dictionary; if the relation set is empty, the value corresponding to relations is an empty list.
        (3) Sorting Priority: The order of entities must strictly follow the order of their first occurrence in the original text.
  ''',

  "sel":'''
    # 2. Input: Text to be extracted (string).
    # 3. Output: Entity and relation extraction results (string) in a custom-designed serialized format.
      ## 3.1 Serialized Output Specification: Ensure all brackets in the output sequence are properly closed and the format meets the requirements! Note that the letter case in entity mentions must strictly match the original text. Do not mistakenly write uppercase letters as lowercase, or lowercase letters as uppercase!
      (1) Overall structure: The outermost layer is []. Nested expressions use square brackets []. Entity/type and relation/tail entity are separated by :; entity blocks are separated by spaces " ", and head entities are separated from relation blocks by spaces " "; all blocks must be fully wrapped in [].If an entity consists of multiple tokens, connect every two tokens with an underscore _.
      (2) Entity block format: Basic format [entity mention:entity type]; only head entities are followed by appended relation blocks, isolated entities have no extra content.
      (3) Relation block format: Format [relation type:tail entity mention], attached after the corresponding head entity block, sorted by the first occurrence order of tail entities in the text.
      (4) Expansion priority: Entity blocks and relation blocks are ordered according to the first occurrence of relevant entities in the text.
      (5) Empty result handling: If no entities are extracted, output only [].
  ''',

  "dfsjson":'''
    # 2. Input: Text to be extracted (string).
    # 3. Output: Entity and relation extraction results (string) in a specially designed serialized format.
      ## 3.1 Serialized Output Specification: Ensure the output conforms to standard JSON syntax, properly closed brackets, complete fields and correct formatting! Note that the letter case in entity mentions must strictly match the original text. Do not mistakenly write uppercase letters as lowercase, or lowercase letters as uppercase!
      (1) Graph traversal logic: Traverse the graph structure using DFS (Depth-First Search). Entities correspond to graph nodes, and relations correspond to directed edges (from head entity to tail entity).
      (2) Overall structure: The output is a JSON list []. Each element in the list represents an independent connected component (i.e., a DFS traversal tree) or an isolated entity.
      (3) Field specifications:
      - span: A field of node, showing the original text of the entity mention (string).
      - type: A field of node, showing the type label of the entity (string).
      - targets: A field of node, showing the list of downstream edges related to the current node. Each element(edge) within the list contains the corresponding relation type and tail entity. 
      - relation: A field of edge(An edge is an element of targets), showing the relation type connecting the corresponding head and tail entity. Only appears in non-root nodes.      
      - ref: Repeated access marker (string). When the DFS path points to a previously defined node, use {"relation": "...", "ref": "entity mention"} without recursively outputting its type and targets.
      (4) Sorting priority: Within the top-level list or the same-level targets, entities must be ordered strictly according to their first occurrence in the original text.
      (5) Top-level node deduplication: If an entity has been visited and defined in a previous DFS path, it is strictly prohibited to appear again as an independent element in the top-level list (i.e., the top-level list does not output "ref" of any visited nodes).
      (6) Empty result handling: If the entity extraction result is empty, output [] directly.
  '''
}


DATASET_2_EXAMPLE_dfs = {
  "ace2005": '''
      ## 3.2 Serialization Output Example:

      (1)text = "Mirjana Markovic , the power behind the scenes during Milosevic 's 13-year reign , is accused of illegally providing their grandson 's nanny with a state - owned luxury apartment in Belgrade in 2000 ."

      (2)Annotation of entities and relations:
      G = {"entities": {"Mirjana Markovic": {"type": "PER"}, "power": {"type": "PER"}, "Milosevic": {"type": "PER"}, "their": {"type": "PER"}, "grandson": {"type": "PER"}, "nanny": {"type": "PER"}, "state": {"type": "GPE"}, "apartment": {"type": "FAC"}, "Belgrade": {"type": "GPE"}}, "relations": [["power", "PER-SOC", "Milosevic"], ["their", "PER-SOC", "grandson"], ["nanny", "ART", "apartment"], ["state", "ART", "apartment"], ["apartment", "PART-WHOLE", "Belgrade"]]}

      (3)The serialized output is:
        [ROOT [Mirjana_Markovic:PER] [power:PER PER-SOC [Milosevic:PER]] [their:PER PER-SOC [grandson:PER]] [nanny:PER ART [apartment:FAC PART-WHOLE [Belgrade:GPE]]] [state:GPE ART [apartment:REF]]]

    # 4.Demonstrations of input and output

      (1)Example 1:
      text = "President Bush points this way today , even the most frivolous of lawsuits cost money , premiums go up and either way , the patient pays ."

      output = [ROOT [President:PER] [Bush:PER] [patient:PER]]

      (2)Example 2:
      text = "the couple is preparing to tie the knot at gracie mansion in new york tonight ."
      
      output = [ROOT [couple:PER PHYS [gracie_mansion:FAC PART-WHOLE [new_york:GPE]]]]
      
      (3)Example 3:
      text = "He was the governor of my state of Texas , where there are a whole lot of doctors ."

      output = [ROOT [He:PER] [governor:PER ORG-AFF [state:GPE]] [my:PER GEN-AFF [state:REF]] [Texas:GPE] [where:GPE] [doctors:PER GEN-AFF [where:REF]]]

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''',

  "conll04":'''
      ## 3.2 Serialization Output Example:

      (1)text = "OSHA had already filed numerous civil charges against the S.A. Healy Co. of McCook , Ill. , the tunnel contractor , and CH2M Hill of Corvallis , Ore. , an engineering firm that supervised the work."
      
      (2)Annotation of entities and relations:
      G = {"entities": {"CH2M Hill": {"type": "org"}, "Corvallis": {"type": "loc"}, "Ill.": {"type": "loc"}, "McCook": {"type": "loc"}, "OSHA": {"type": "org"}, "Ore.": {"type": "loc"}, "S.A. Healy Co.": {"type": "org"}}, "relations": [["CH2M Hill", "orgbased_in", "Corvallis"], ["CH2M Hill", "orgbased_in", "Ore."], ["Corvallis", "located_in", "Ore."], ["McCook", "located_in", "Ill."], ["S.A. Healy Co.", "orgbased_in", "McCook"], ["S.A. Healy Co.", "orgbased_in", "Ill."]]}
      
      (3)The serialized output is:
      [ROOT [OSHA:org] [S.A._Healy_Co.:org orgbased_in [McCook:loc located_in [Ill.:loc]] orgbased_in [Ill.:REF]] [CH2M_Hill:org orgbased_in [Corvallis:loc located_in [Ore.:loc]] orgbased_in [Ore.:REF]]]

    # 4.Demonstrations of input and output

    (1)Example 1:
    text= "The strong Santa Ana winds that earlier produced wind gusts as high as 100 mph in Southern California , destroying a blimp , shutting down an airport , and cutting power to thousands of utility customers were subsiding , officials said .",

    output = [ROOT [Santa_Ana:loc located_in [Southern_California:loc]] [100_mph:other]]

    (2)Example 2:
    text = "Meanwhile , Shi Liming at the Institute of Zoology of Kunming found that pandas lack variety in their protein heredity , which may serve as one of the major reasons for pandas ' near extinction .",
    
    output = [ROOT [Shi_Liming:peop work_for [Institute_of_Zoology:org orgbased_in [Kunming:loc]]]]

    (3) Example 3:
    text = "The Globe and Mail , which calls itself Canada 's national newspaper , said in an editorial Thursday that Quebec Premier Robert Bourassa ` ` has received , and deserves , strong criticism for his decision on the language of commercial signs in Quebec. .. .", 

    output = [ROOT [The_Globe_and_Mail:org orgbased_in [Canada:loc]] [Quebec:loc] [Robert_Bourassa:peop live_in [Canada:REF] live_in [Quebec:REF] live_in [Quebec.:loc]]]
    
    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''', 

  "scierc":'''      
      ## 3.2 Serialization Output Example:

        (1)text = "This paper presents an algorithm for labeling curvilinear structure at multiple scales in line drawings and edge images Symbolic CURVE-ELEMENT tokens residing in a spatially-indexed and scale-indexed data structure denote circular arcs fit to image data ."

        (2)Annotation of entities and relations:
        G = {"entities": {"algorithm": {"type": "Generic"}, "labeling curvilinear structure": {"type": "Task"}, "line drawings": {"type": "Material"}, "edge images": {"type": "Material"}, "CURVE-ELEMENT tokens": {"type": "OtherScientificTerm"}, "spatially-indexed and scale-indexed data structure": {"type": "OtherScientificTerm"}, "image data": {"type": "Material"}}, "relations": [["algorithm", "USED-FOR", "labeling curvilinear structure"], ["line drawings", "FEATURE-OF", "labeling curvilinear structure"], ["line drawings", "CONJUNCTION", "edge images"], ["edge images", "FEATURE-OF", "labeling curvilinear structure"], ["CURVE-ELEMENT tokens", "PART-OF", "spatially-indexed and scale-indexed data structure"]]}
        
        (3)The serialized output is:
        [ROOT [algorithm:Generic USED-FOR [labeling_curvilinear_structure:Task]] [line_drawings:Material FEATURE-OF [labeling_curvilinear_structure:REF] CONJUNCTION [edge_images:Material FEATURE-OF [labeling_curvilinear_structure:REF]]] [CURVE-ELEMENT_tokens:OtherScientificTerm PART-OF [spatially-indexed_and_scale-indexed_data_structure:OtherScientificTerm]] [image_data:Material]]
     
      # 4.Demonstrations of input and output

      (1)Example 1:
      text = "Considering the size , we utilized acoustic vector sensor -LRB- AVS -RRB- and proposed a DOA estimation algorithm previously -LSB- 1 -RSB- , offering high accuracy with larger-than-15dB SNR but is deteriorated by non-speech interferences -LRB- NSI -RRB- ."

      output = [ROOT [acoustic_vector_sensor_-LRB-_AVS_-RRB-:Method] [DOA_estimation_algorithm:Method] [non-speech_interferences_-LRB-_NSI_-RRB-:OtherScientificTerm]]

      (2)Example 2:
      text = "CriterionSM Online Essay Evaluation Service includes a capability that labels sentences in student writing with essay-based discourse elements -LRB- e.g. , thesis statements -RRB- ."

      output = [ROOT [CriterionSM_Online_Essay_Evaluation_Service:Task] [essay-based_discourse_elements:OtherScientificTerm PART-OF [CriterionSM_Online_Essay_Evaluation_Service:REF]] [thesis_statements:OtherScientificTerm HYPONYM-OF [essay-based_discourse_elements:REF]]]

      (3) Example 3:
      text = "This system identifies features of sentences based on semantic similarity measures and discourse structure .",

      output = [ROOT [system:Generic USED-FOR [features:OtherScientificTerm]] [semantic_similarity_measures:Metric USED-FOR [features:REF]] [discourse_structure:OtherScientificTerm USED-FOR [features:REF] CONJUNCTION [semantic_similarity_measures:REF]]]

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''',


  "ade":'''
      ## 3.2 Serialization Output Example:

      (1)text = "Hypersensitivity to aspirin can be manifested as acute asthma , urticaria and/or angioedema , or a systemic anaphylactoid reaction ."

      (2)Annotation of entities and relations:
      G = {"entities": {"aspirin": {"type": "Drug"}, "urticaria": {"type": "Adverse-Effect"}, "angioedema": {"type": "Adverse-Effect"}, "systemic anaphylactoid reaction": {"type": "Adverse-Effect"}}, "relations": [["urticaria", "adverse-reaction-of", "aspirin"], ["angioedema", "adverse-reaction-of", "aspirin"], ["systemic anaphylactoid reaction", "adverse-reaction-of", "aspirin"]]}

      (3)The serialized output is:
       [ROOT [aspirin:Drug] [urticaria:Adverse-Effect adverse-reaction-of [aspirin:REF]] [angioedema:Adverse-Effect adverse-reaction-of [aspirin:REF]] [systemic_anaphylactoid_reaction:Adverse-Effect adverse-reaction-of [aspirin:REF]]]

    # 4.Demonstrations of input and output

    (1)Example 1:
    text = "The mechanism of anaphylactoid reaction to zomepirac in this case , therefore , remains unclear ."

     output = [ROOT [anaphylactoid_reaction:Adverse-Effect adverse-reaction-of [zomepirac:Drug]]]

    (2)Example 2:
    text = "CONCLUSIONS : In our reported case , a local hyperproduction of TNF - alpha from macrophages that was induced by the injected insulin could explain the dedifferentiation of the adipocytes of the subcutaneous tissue and the reversion that was induced by the local injection of dexamethasone ."

    output =  [ROOT [hyperproduction_of_TNF_-_alpha:Adverse-Effect adverse-reaction-of [insulin:Drug]] [dedifferentiation_of_the_adipocytes:Adverse-Effect adverse-reaction-of [insulin:REF]]]

    (3)Example 3:
    text = "During clarithromycin coadministration , four out of the seven patients developed moderate - to - severe toxic symptoms of carbamazepine , such as drowsiness , dizziness , and ataxia , which resolved within 5 days after clarithromycin discontinuation ."

    output =  [ROOT [clarithromycin:Drug] [toxic_symptoms:Adverse-Effect adverse-reaction-of [clarithromycin:REF] adverse-reaction-of [carbamazepine:Drug]] [drowsiness:Adverse-Effect adverse-reaction-of [clarithromycin:REF] adverse-reaction-of [carbamazepine:REF]] [dizziness:Adverse-Effect adverse-reaction-of [clarithromycin:REF] adverse-reaction-of [carbamazepine:REF]] [ataxia:Adverse-Effect adverse-reaction-of [clarithromycin:REF] adverse-reaction-of [carbamazepine:REF]]]

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
  '''  
}

DATASET_2_EXAMPLE_naive = {
  "ace2005": '''
      ## 3.2 Serialization Output Example:

      (1)text = "Mirjana Markovic , the power behind the scenes during Milosevic 's 13-year reign , is accused of illegally providing their grandson 's nanny with a state - owned luxury apartment in Belgrade in 2000 ."

      (2)Annotation of entities and relations:G = {
           "entities": {"Mirjana Markovic": {"type": "PER"}, "power": {"type": "PER"}, "Milosevic": {"type": "PER"}, "their": {"type": "PER"}, "grandson": {"type": "PER"}, "nanny": {"type": "PER"}, "state": {"type": "GPE"}, "apartment": {"type": "FAC"}, "Belgrade": {"type": "GPE"}}, "relations": [["power", "PER-SOC", "Milosevic"], ["their", "PER-SOC", "grandson"], ["nanny", "ART", "apartment"], ["state", "ART", "apartment"], ["apartment", "PART-WHOLE", "Belgrade"]]}

      (3)The serialized output is:
      {"entities": {"Mirjana Markovic": {"type": "PER"}, "power": {"type": "PER"}, "Milosevic": {"type": "PER"}, "their": {"type": "PER"}, "grandson": {"type": "PER"}, "nanny": {"type": "PER"}, "state": {"type": "GPE"}, "apartment": {"type": "FAC"}, "Belgrade": {"type": "GPE"}}, "relations": [["power", "PER-SOC", "Milosevic"], ["their", "PER-SOC", "grandson"], ["nanny", "ART", "apartment"], ["state", "ART", "apartment"], ["apartment", "PART-WHOLE", "Belgrade"]]}

    # 4.Demonstrations of input and output

      (1)Example 1:
      text = "President Bush points this way today , even the most frivolous of lawsuits cost money , premiums go up and either way , the patient pays ."

      output = {"entities": {"President": {"type": "PER"}, "Bush": {"type": "PER"}, "patient": {"type": "PER"}}, "relations": []}

      (2)Example 2:
      text = "the couple is preparing to tie the knot at gracie mansion in new york tonight ."
      
      output = {"entities": {"couple": {"type": "PER"}, "gracie mansion": {"type": "FAC"}, "new york": {"type": "GPE"}}, "relations": [["couple", "PHYS", "gracie mansion"], ["gracie mansion", "PART-WHOLE", "new york"]]}
      
      (3)Example 3:
      text = "He was the governor of my state of Texas , where there are a whole lot of doctors ."

      output = {"entities": {"He": {"type": "PER"}, "governor": {"type": "PER"}, "my": {"type": "PER"}, "state": {"type": "GPE"}, "Texas": {"type": "GPE"}, "where": {"type": "GPE"}, "doctors": {"type": "PER"}}, "relations": [["governor", "ORG-AFF", "state"], ["my", "GEN-AFF", "state"], ["doctors", "GEN-AFF", "where"]]}
      
    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''',

  "conll04":'''
      ## 3.2 Serialization Output Example:

      (1)text = "OSHA had already filed numerous civil charges against the S.A. Healy Co. of McCook , Ill. , the tunnel contractor , and CH2M Hill of Corvallis , Ore. , an engineering firm that supervised the work."

      (2)Annotation of entities and relations:
      G = {"entities": {"CH2M Hill": {"type": "org"}, "Corvallis": {"type": "loc"}, "Ill.": {"type": "loc"}, "McCook": {"type": "loc"}, "OSHA": {"type": "org"}, "Ore.": {"type": "loc"}, "S.A. Healy Co.": {"type": "org"}}, "relations": [["CH2M Hill", "orgbased_in", "Corvallis"], ["CH2M Hill", "orgbased_in", "Ore."], ["Corvallis", "located_in", "Ore."], ["McCook", "located_in", "Ill."], ["S.A. Healy Co.", "orgbased_in", "McCook"], ["S.A. Healy Co.", "orgbased_in", "Ill."]]}

      (3)The serialized output is: 
      {"entities": {"OSHA": {"type": "org"}, "S.A. Healy Co.": {"type": "org"}, "McCook": {"type": "loc"}, "Ill.": {"type": "loc"}, "CH2M Hill": {"type": "org"}, "Corvallis": {"type": "loc"}, "Ore.": {"type": "loc"}}, "relations": [["S.A. Healy Co.", "orgbased_in", "McCook"], ["S.A. Healy Co.", "orgbased_in", "Ill."], ["McCook", "located_in", "Ill."], ["CH2M Hill", "orgbased_in", "Corvallis"], ["CH2M Hill", "orgbased_in", "Ore."], ["Corvallis", "located_in", "Ore."]]}
    
    # 4.Demonstrations of input and output
    
      (1)Example 1:
      text = "The strong Santa Ana winds that earlier produced wind gusts as high as 100 mph in Southern California , destroying a blimp , shutting down an airport , and cutting power to thousands of utility customers were subsiding , officials said ."

      output = {"entities": {"Santa Ana": {"type": "loc"}, "100 mph": {"type": "other"}, "Southern California": {"type": "loc"}}, "relations": [["Santa Ana", "located_in", "Southern California"]]}

      (2)Example 2:
      text = "Meanwhile , Shi Liming at the Institute of Zoology of Kunming found that pandas lack variety in their protein heredity , which may serve as one of the major reasons for pandas ' near extinction ."
      
      output = {"entities": {"Shi Liming": {"type": "peop"}, "Institute of Zoology": {"type": "org"}, "Kunming": {"type": "loc"}}, "relations": [["Shi Liming", "work_for", "Institute of Zoology"], ["Institute of Zoology", "orgbased_in", "Kunming"]]}
      
      (3)Example 3:
      text = "The Globe and Mail , which calls itself Canada 's national newspaper , said in an editorial Thursday that Quebec Premier Robert Bourassa ` ` has received , and deserves , strong criticism for his decision on the language of commercial signs in Quebec. .. ."

      output = {"entities": {"The Globe and Mail": {"type": "org"}, "Canada": {"type": "loc"}, "Quebec": {"type": "loc"}, "Robert Bourassa": {"type": "peop"}, "Quebec.": {"type": "loc"}}, "relations": [["The Globe and Mail", "orgbased_in", "Canada"], ["Robert Bourassa", "live_in", "Canada"], ["Robert Bourassa", "live_in", "Quebec"], ["Robert Bourassa", "live_in", "Quebec."]]}

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''', 

  "scierc":'''
      ## 3.2 Serialization Output Example:
      
        (1)text = "This paper presents an algorithm for labeling curvilinear structure at multiple scales in line drawings and edge images Symbolic CURVE-ELEMENT tokens residing in a spatially-indexed and scale-indexed data structure denote circular arcs fit to image data ."

        (2)Annotation of entities and relations:
        G = {"entities": {"algorithm": {"type": "Generic"}, "labeling curvilinear structure": {"type": "Task"}, "line drawings": {"type": "Material"}, "edge images": {"type": "Material"}, "CURVE-ELEMENT tokens": {"type": "OtherScientificTerm"}, "spatially-indexed and scale-indexed data structure": {"type": "OtherScientificTerm"}, "image data": {"type": "Material"}}, "relations": [["algorithm", "USED-FOR", "labeling curvilinear structure"], ["line drawings", "FEATURE-OF", "labeling curvilinear structure"], ["line drawings", "CONJUNCTION", "edge images"], ["edge images", "FEATURE-OF", "labeling curvilinear structure"], ["CURVE-ELEMENT tokens", "PART-OF", "spatially-indexed and scale-indexed data structure"]]}
        
        (3)The serialized output is:
        {"entities": {"algorithm": {"type": "Generic"}, "labeling curvilinear structure": {"type": "Task"}, "line drawings": {"type": "Material"}, "edge images": {"type": "Material"}, "CURVE-ELEMENT tokens": {"type": "OtherScientificTerm"}, "spatially-indexed and scale-indexed data structure": {"type": "OtherScientificTerm"}, "image data": {"type": "Material"}}, "relations": [["algorithm", "USED-FOR", "labeling curvilinear structure"], ["line drawings", "FEATURE-OF", "labeling curvilinear structure"], ["line drawings", "CONJUNCTION", "edge images"], ["edge images", "FEATURE-OF", "labeling curvilinear structure"], ["CURVE-ELEMENT tokens", "PART-OF", "spatially-indexed and scale-indexed data structure"]]}
      
      # 4.Demonstrations of input and output

      (1)Example 1:
      text = "Considering the size , we utilized acoustic vector sensor -LRB- AVS -RRB- and proposed a DOA estimation algorithm previously -LSB- 1 -RSB- , offering high accuracy with larger-than-15dB SNR but is deteriorated by non-speech interferences -LRB- NSI -RRB- ."

      output = {"entities": {"acoustic vector sensor -LRB- AVS -RRB-": {"type": "Method"}, "DOA estimation algorithm": {"type": "Method"}, "non-speech interferences -LRB- NSI -RRB-": {"type": "OtherScientificTerm"}}, "relations": []}

      (2)Example 2:
      text = "CriterionSM Online Essay Evaluation Service includes a capability that labels sentences in student writing with essay-based discourse elements -LRB- e.g. , thesis statements -RRB- ."

      output = {"entities": {"CriterionSM Online Essay Evaluation Service": {"type": "Task"}, "essay-based discourse elements": {"type": "OtherScientificTerm"}, "thesis statements": {"type": "OtherScientificTerm"}}, "relations": [["essay-based discourse elements", "PART-OF", "CriterionSM Online Essay Evaluation Service"], ["thesis statements", "HYPONYM-OF", "essay-based discourse elements"]]}

      (3) Example 3:
      text = "This system identifies features of sentences based on semantic similarity measures and discourse structure .",

      output = {"entities": {"system": {"type": "Generic"}, "features": {"type": "OtherScientificTerm"}, "semantic similarity measures": {"type": "Metric"}, "discourse structure": {"type": "OtherScientificTerm"}}, "relations": [["system", "USED-FOR", "features"], ["semantic similarity measures", "USED-FOR", "features"], ["discourse structure", "USED-FOR", "features"], ["discourse structure", "CONJUNCTION", "semantic similarity measures"]]}

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''',

  "ade":'''     
      ## 3.2 Serialization Output Example:

      (1)text = "Hypersensitivity to aspirin can be manifested as acute asthma , urticaria and/or angioedema , or a systemic anaphylactoid reaction ."

      (2)Annotation of entities and relations:
      G = {"entities": {"aspirin": {"type": "Drug"}, "urticaria": {"type": "Adverse-Effect"}, "angioedema": {"type": "Adverse-Effect"}, "systemic anaphylactoid reaction": {"type": "Adverse-Effect"}}, "relations": [["urticaria", "adverse-reaction-of", "aspirin"], ["angioedema", "adverse-reaction-of", "aspirin"], ["systemic anaphylactoid reaction", "adverse-reaction-of", "aspirin"]]}

      (3)The serialized output is:
       {"entities": {"aspirin": {"type": "Drug"}, "urticaria": {"type": "Adverse-Effect"}, "angioedema": {"type": "Adverse-Effect"}, "systemic anaphylactoid reaction": {"type": "Adverse-Effect"}}, "relations": [["urticaria", "adverse-reaction-of", "aspirin"], ["angioedema", "adverse-reaction-of", "aspirin"], ["systemic anaphylactoid reaction", "adverse-reaction-of", "aspirin"]]}

    # 4.Demonstrations of input and output

      (1)Example 1:
      text = "The mechanism of anaphylactoid reaction to zomepirac in this case , therefore , remains unclear ."

      output = {"entities": {"anaphylactoid reaction": {"type": "Adverse-Effect"}, "zomepirac": {"type": "Drug"}}, "relations": [["anaphylactoid reaction", "adverse-reaction-of", "zomepirac"]]}

      (2)Example 2:
      text = "CONCLUSIONS : In our reported case , a local hyperproduction of TNF - alpha from macrophages that was induced by the injected insulin could explain the dedifferentiation of the adipocytes of the subcutaneous tissue and the reversion that was induced by the local injection of dexamethasone ."

      output =  {"entities": {"hyperproduction of TNF - alpha": {"type": "Adverse-Effect"}, "insulin": {"type": "Drug"}, "dedifferentiation of the adipocytes": {"type": "Adverse-Effect"}}, "relations": [["hyperproduction of TNF - alpha", "adverse-reaction-of", "insulin"], ["dedifferentiation of the adipocytes", "adverse-reaction-of", "insulin"]]}

      (3)Example 3:
      text = "During clarithromycin coadministration , four out of the seven patients developed moderate - to - severe toxic symptoms of carbamazepine , such as drowsiness , dizziness , and ataxia , which resolved within 5 days after clarithromycin discontinuation ."

      output =  {"entities": {"clarithromycin": {"type": "Drug"}, "toxic symptoms": {"type": "Adverse-Effect"}, "carbamazepine": {"type": "Drug"}, "drowsiness": {"type": "Adverse-Effect"}, "dizziness": {"type": "Adverse-Effect"}, "ataxia": {"type": "Adverse-Effect"}}, "relations": [["toxic symptoms", "adverse-reaction-of", "clarithromycin"], ["toxic symptoms", "adverse-reaction-of", "carbamazepine"], ["drowsiness", "adverse-reaction-of", "clarithromycin"], ["drowsiness", "adverse-reaction-of", "carbamazepine"], ["dizziness", "adverse-reaction-of", "clarithromycin"], ["dizziness", "adverse-reaction-of", "carbamazepine"], ["ataxia", "adverse-reaction-of", "clarithromycin"], ["ataxia", "adverse-reaction-of", "carbamazepine"]]}

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
  '''
}

DATASET_2_EXAMPLE_sel = {
  "ace2005": '''
      ## 3.2 Serialization Output Example :

      (1)text = "Mirjana Markovic , the power behind the scenes during Milosevic 's 13-year reign , is accused of illegally providing their grandson 's nanny with a state - owned luxury apartment in Belgrade in 2000 ."
      (2)Annotation of entities and relations:
      G = {"entities": {"Mirjana Markovic": {"type": "PER"}, "power": {"type": "PER"}, "Milosevic": {"type": "PER"}, "their": {"type": "PER"}, "grandson": {"type": "PER"}, "nanny": {"type": "PER"}, "state": {"type": "GPE"}, "apartment": {"type": "FAC"}, "Belgrade": {"type": "GPE"}}, "relations": [["power", "PER-SOC", "Milosevic"], ["their", "PER-SOC", "grandson"], ["nanny", "ART", "apartment"], ["state", "ART", "apartment"], ["apartment", "PART-WHOLE", "Belgrade"]]}

      (3)The serialized output is:
      [ROOT [Mirjana_Markovic:PER] [power:PER [PER-SOC:Milosevic]] [Milosevic:PER] [their:PER [PER-SOC:grandson]] [grandson:PER] [nanny:PER [ART:apartment]] [state:GPE [ART:apartment]] [apartment:FAC [PART-WHOLE:Belgrade]] [Belgrade:GPE]]
        
      # 4.Demonstrations of input and output

      (1)Example 1:
      text = "President Bush points this way today , even the most frivolous of lawsuits cost money , premiums go up and either way , the patient pays ."

      output = [ROOT [President:PER] [Bush:PER] [patient:PER]]

      (2)Example 2:
      text = "the couple is preparing to tie the knot at gracie mansion in new york tonight ."
      
      output = [ROOT [couple:PER [PHYS:gracie_mansion]] [gracie_mansion:FAC [PART-WHOLE:new_york]] [new_york:GPE]]
      
      (3)Example 3:
      text = "He was the governor of my state of Texas , where there are a whole lot of doctors ."
      
      output = [ROOT [He:PER] [governor:PER [ORG-AFF:state]] [my:PER [GEN-AFF:state]] [state:GPE] [Texas:GPE] [where:GPE] [doctors:PER [GEN-AFF:where]]]
    
    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
      ''',

  "conll04":'''
    ## 3.2 Serialization Output Example:

    (1)text = "OSHA had already filed numerous civil charges against the S.A. Healy Co. of McCook , Ill. , the tunnel contractor , and CH2M Hill of Corvallis , Ore. , an engineering firm that supervised the work."

    (2)Annotation of entities and relations:
    G = {"entities": {"CH2M Hill": {"type": "org"}, "Corvallis": {"type": "loc"}, "Ill.": {"type": "loc"}, "McCook": {"type": "loc"}, "OSHA": {"type": "org"}, "Ore.": {"type": "loc"}, "S.A. Healy Co.": {"type": "org"}}, "relations": [["CH2M Hill", "orgbased_in", "Corvallis"], ["CH2M Hill", "orgbased_in", "Ore."], ["Corvallis", "located_in", "Ore."], ["McCook", "located_in", "Ill."], ["S.A. Healy Co.", "orgbased_in", "McCook"], ["S.A. Healy Co.", "orgbased_in", "Ill."]]}

    (3)The serialized output is: 
    [ROOT [OSHA:org] [S.A._Healy_Co.:org [orgbased_in:McCook] [orgbased_in:Ill.]] [McCook:loc [located_in:Ill.]] [Ill.:loc] [CH2M_Hill:org [orgbased_in:Corvallis] [orgbased_in:Ore.]] [Corvallis:loc [located_in:Ore.]] [Ore.:loc]]

    # 4.Demonstrations of input and output

    (1)Example 1:
    text = "The strong Santa Ana winds that earlier produced wind gusts as high as 100 mph in Southern California , destroying a blimp , shutting down an airport , and cutting power to thousands of utility customers were subsiding , officials said .",

    output = [ROOT [Santa_Ana:loc [located_in:Southern_California]] [100_mph:other] [Southern_California:loc]]
    
    (2)Example 2:
    text = "Meanwhile , Shi Liming at the Institute of Zoology of Kunming found that pandas lack variety in their protein heredity , which may serve as one of the major reasons for pandas ' near extinction .",
    
    output = [ROOT [Shi_Liming:peop [work_for:Institute_of_Zoology]] [Institute_of_Zoology:org [orgbased_in:Kunming]] [Kunming:loc]]
    
    (3) Example 3:
    text = "The Globe and Mail , which calls itself Canada 's national newspaper , said in an editorial Thursday that Quebec Premier Robert Bourassa ` ` has received , and deserves , strong criticism for his decision on the language of commercial signs in Quebec. .. .", 
    
    output = [ROOT [The_Globe_and_Mail:org [orgbased_in:Canada]] [Canada:loc] [Quebec:loc] [Robert_Bourassa:peop [live_in:Canada] [live_in:Quebec] [live_in:Quebec.]] [Quebec.:loc]]

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''', 

  "scierc":'''
      ## 3.2 Serialization Output Example:
        (1)text = "This paper presents an algorithm for labeling curvilinear structure at multiple scales in line drawings and edge images Symbolic CURVE-ELEMENT tokens residing in a spatially-indexed and scale-indexed data structure denote circular arcs fit to image data ."
        
        (2)Annotation of entities and relations:
        G = {"entities": {"algorithm": {"type": "Generic"}, "labeling curvilinear structure": {"type": "Task"}, "line drawings": {"type": "Material"}, "edge images": {"type": "Material"}, "CURVE-ELEMENT tokens": {"type": "OtherScientificTerm"}, "spatially-indexed and scale-indexed data structure": {"type": "OtherScientificTerm"}, "image data": {"type": "Material"}}, "relations": [["algorithm", "USED-FOR", "labeling curvilinear structure"], ["line drawings", "FEATURE-OF", "labeling curvilinear structure"], ["line drawings", "CONJUNCTION", "edge images"], ["edge images", "FEATURE-OF", "labeling curvilinear structure"], ["CURVE-ELEMENT tokens", "PART-OF", "spatially-indexed and scale-indexed data structure"]]}
        
        (3)The serialized output is:
        [ROOT [algorithm:Generic [USED-FOR:labeling_curvilinear_structure]] [labeling_curvilinear_structure:Task] [line_drawings:Material [FEATURE-OF:labeling_curvilinear_structure] [CONJUNCTION:edge_images]] [edge_images:Material [FEATURE-OF:labeling_curvilinear_structure]] [CURVE-ELEMENT_tokens:OtherScientificTerm [PART-OF:spatially-indexed_and_scale-indexed_data_structure]] [spatially-indexed_and_scale-indexed_data_structure:OtherScientificTerm] [image_data:Material]]
     
      # 4.Demonstrations of input and output
      (1)Example1:
      text = "Considering the size , we utilized acoustic vector sensor -LRB- AVS -RRB- and proposed a DOA estimation algorithm previously -LSB- 1 -RSB- , offering high accuracy with larger-than-15dB SNR but is deteriorated by non-speech interferences -LRB- NSI -RRB- ."

      output = [ROOT [acoustic_vector_sensor_-LRB-_AVS_-RRB-:Method] [DOA_estimation_algorithm:Method] [non-speech_interferences_-LRB-_NSI_-RRB-:OtherScientificTerm]]

      (2)Example2:
      text = "CriterionSM Online Essay Evaluation Service includes a capability that labels sentences in student writing with essay-based discourse elements -LRB- e.g. , thesis statements -RRB- ."

      output = [ROOT [CriterionSM_Online_Essay_Evaluation_Service:Task] [essay-based_discourse_elements:OtherScientificTerm [PART-OF:CriterionSM_Online_Essay_Evaluation_Service]] [thesis_statements:OtherScientificTerm [HYPONYM-OF:essay-based_discourse_elements]]]

      (3) Example 3:
      text = "This system identifies features of sentences based on semantic similarity measures and discourse structure .",

      output = [ROOT [system:Generic [USED-FOR:features]] [features:OtherScientificTerm] [semantic_similarity_measures:Metric [USED-FOR:features]] [discourse_structure:OtherScientificTerm [USED-FOR:features] [CONJUNCTION:semantic_similarity_measures]]]

      # 以下为测试样本，请输出序列化后的测试结果(字符串)，不要输出多余的内容。确保输出的标签在给出的7种实体标签与6种关系标签之中！确保输出序列的括号正确闭合、格式符合要求！
    '''
  ,

  "ade":'''
      ## 3.2 Serialization Output Example:

      (1)text = "Hypersensitivity to aspirin can be manifested as acute asthma , urticaria and/or angioedema , or a systemic anaphylactoid reaction ."

      (2)Annotation of entities and relations:
      G = {"entities": {"aspirin": {"type": "Drug"}, "urticaria": {"type": "Adverse-Effect"}, "angioedema": {"type": "Adverse-Effect"}, "systemic anaphylactoid reaction": {"type": "Adverse-Effect"}}, "relations": [["urticaria", "adverse-reaction-of", "aspirin"], ["angioedema", "adverse-reaction-of", "aspirin"], ["systemic anaphylactoid reaction", "adverse-reaction-of", "aspirin"]]}

      (3)The serialized output is:
       [ROOT [aspirin:Drug] [urticaria:Adverse-Effect [adverse-reaction-of:aspirin]] [angioedema:Adverse-Effect [adverse-reaction-of:aspirin]] [systemic_anaphylactoid_reaction:Adverse-Effect [adverse-reaction-of:aspirin]]]

    # 4.Demonstrations of input and output

      (1)Example 1:
      text = "The mechanism of anaphylactoid reaction to zomepirac in this case , therefore , remains unclear ."

      output = [ROOT [anaphylactoid_reaction:Adverse-Effect [adverse-reaction-of:zomepirac]] [zomepirac:Drug]]

      (2)Example 2:
      text = "CONCLUSIONS : In our reported case , a local hyperproduction of TNF - alpha from macrophages that was induced by the injected insulin could explain the dedifferentiation of the adipocytes of the subcutaneous tissue and the reversion that was induced by the local injection of dexamethasone ."

      output =  [ROOT [hyperproduction_of_TNF_-_alpha:Adverse-Effect [adverse-reaction-of:insulin]] [insulin:Drug] [dedifferentiation_of_the_adipocytes:Adverse-Effect [adverse-reaction-of:insulin]]]

      (3)Example 3:
      text = "During clarithromycin coadministration , four out of the seven patients developed moderate - to - severe toxic symptoms of carbamazepine , such as drowsiness , dizziness , and ataxia , which resolved within 5 days after clarithromycin discontinuation ."

      output =  [ROOT [clarithromycin:Drug] [toxic_symptoms:Adverse-Effect [adverse-reaction-of:clarithromycin] [adverse-reaction-of:carbamazepine]] [carbamazepine:Drug] [drowsiness:Adverse-Effect [adverse-reaction-of:clarithromycin] [adverse-reaction-of:carbamazepine]] [dizziness:Adverse-Effect [adverse-reaction-of:clarithromycin] [adverse-reaction-of:carbamazepine]] [ataxia:Adverse-Effect [adverse-reaction-of:clarithromycin] [adverse-reaction-of:carbamazepine]]]

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
  '''
}

DATASET_2_EXAMPLE_dfsjson = {
  "ace2005": '''
      ## 3.2 Serialization Output Example:

      (1)text = "Mirjana Markovic , the power behind the scenes during Milosevic 's 13-year reign , is accused of illegally providing their grandson 's nanny with a state - owned luxury apartment in Belgrade in 2000 ."

      (2)Annotation of entities and relations:
      G = {"entities": {"Mirjana Markovic": {"type": "PER"}, "power": {"type": "PER"}, "Milosevic": {"type": "PER"}, "their": {"type": "PER"}, "grandson": {"type": "PER"}, "nanny": {"type": "PER"}, "state": {"type": "GPE"}, "apartment": {"type": "FAC"}, "Belgrade": {"type": "GPE"}}, "relations": [["power", "PER-SOC", "Milosevic"], ["their", "PER-SOC", "grandson"], ["nanny", "ART", "apartment"], ["state", "ART", "apartment"], ["apartment", "PART-WHOLE", "Belgrade"]]}

      (3)The serialized output is:
      [{"span": "Mirjana Markovic", "type": "PER"}, {"span": "power", "type": "PER", "targets": [{"relation": "PER-SOC", "span": "Milosevic", "type": "PER"}]}, {"span": "their", "type": "PER", "targets": [{"relation": "PER-SOC", "span": "grandson", "type": "PER"}]}, {"span": "nanny", "type": "PER", "targets": [{"relation": "ART", "span": "apartment", "type": "FAC", "targets": [{"relation": "PART-WHOLE", "span": "Belgrade", "type": "GPE"}]}]}, {"span": "state", "type": "GPE", "targets": [{"relation": "ART", "ref": "apartment"}]}]
    
    # 4.Demonstrations of input and output

      (1)Example 1:
      text = "President Bush points this way today , even the most frivolous of lawsuits cost money , premiums go up and either way , the patient pays ."

      output = [{"span": "President", "type": "PER"}, {"span": "Bush", "type": "PER"}, {"span": "patient", "type": "PER"}]

      (2)Example 2:
      text = "the couple is preparing to tie the knot at gracie mansion in new york tonight ."
      
      output = [{"span": "couple", "type": "PER", "targets": [{"relation": "PHYS", "span": "gracie mansion", "type": "FAC", "targets": [{"relation": "PART-WHOLE", "span": "new york", "type": "GPE"}]}]}]

      (3)Example 3:
      text = "He was the governor of my state of Texas , where there are a whole lot of doctors ."
      
      output = [{"span": "He", "type": "PER"}, {"span": "governor", "type": "PER", "targets": [{"relation": "ORG-AFF", "span": "state", "type": "GPE"}]}, {"span": "my", "type": "PER", "targets": [{"relation": "GEN-AFF", "ref": "state"}]}, {"span": "Texas", "type": "GPE"}, {"span": "where", "type": "GPE"}, {"span": "doctors", "type": "PER", "targets": [{"relation": "GEN-AFF", "ref": "where"}]}]
    
    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
    # Below is the test sample: 
    ''',

  "conll04":'''
      ## 3.2 Serialization Output Example:

      (1)text = "OSHA had already filed numerous civil charges against the S.A. Healy Co. of McCook , Ill. , the tunnel contractor , and CH2M Hill of Corvallis , Ore. , an engineering firm that supervised the work."

      (2)Annotation of entities and relations:
      G = {"entities": {"CH2M Hill": {"type": "org"}, "Corvallis": {"type": "loc"}, "Ill.": {"type": "loc"}, "McCook": {"type": "loc"}, "OSHA": {"type": "org"}, "Ore.": {"type": "loc"}, "S.A. Healy Co.": {"type": "org"}}, "relations": [["CH2M Hill", "orgbased_in", "Corvallis"], ["CH2M Hill", "orgbased_in", "Ore."], ["Corvallis", "located_in", "Ore."], ["McCook", "located_in", "Ill."], ["S.A. Healy Co.", "orgbased_in", "McCook"], ["S.A. Healy Co.", "orgbased_in", "Ill."]]}

      (3)The serialized output is: 
      [{"span": "OSHA", "type": "org"}, {"span": "S.A. Healy Co.", "type": "org", "targets": [{"relation": "orgbased_in", "span": "McCook", "type": "loc", "targets": [{"relation": "located_in", "span": "Ill.", "type": "loc"}]}, {"relation": "orgbased_in", "ref": "Ill."}]}, {"span": "CH2M Hill", "type": "org", "targets": [{"relation": "orgbased_in", "span": "Corvallis", "type": "loc", "targets": [{"relation": "located_in", "span": "Ore.", "type": "loc"}]}, {"relation": "orgbased_in", "ref": "Ore."}]}]

    # 4.Demonstrations of input and output

      (1)Example 1:
      text = "The strong Santa Ana winds that earlier produced wind gusts as high as 100 mph in Southern California , destroying a blimp , shutting down an airport , and cutting power to thousands of utility customers were subsiding , officials said .",

      output = [{"span": "Santa Ana", "type": "loc", "targets": [{"relation": "located_in", "span": "Southern California", "type": "loc"}]}, {"span": "100 mph", "type": "other"}]

      (2)Example 2:
      text = "Meanwhile , Shi Liming at the Institute of Zoology of Kunming found that pandas lack variety in their protein heredity , which may serve as one of the major reasons for pandas ' near extinction .",
      
      output = [{"span": "Shi Liming", "type": "peop", "targets": [{"relation": "work_for", "span": "Institute of Zoology", "type": "org", "targets": [{"relation": "orgbased_in", "span": "Kunming", "type": "loc"}]}]}]
      
      (3) Example 3:
      text = "The Globe and Mail , which calls itself Canada 's national newspaper , said in an editorial Thursday that Quebec Premier Robert Bourassa ` ` has received , and deserves , strong criticism for his decision on the language of commercial signs in Quebec. .. .", 
      
      output = [{"span": "The Globe and Mail", "type": "org", "targets": [{"relation": "orgbased_in", "span": "Canada", "type": "loc"}]}, {"span": "Quebec", "type": "loc"}, {"span": "Robert Bourassa", "type": "peop", "targets": [{"relation": "live_in", "ref": "Canada"}, {"relation": "live_in", "ref": "Quebec"}, {"relation": "live_in", "span": "Quebec.", "type": "loc"}]}]

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
      # Below is the test sample: 
    ''', 

  "scierc":'''     
      ## 3.2 Serialization Output Example:

        (1)text = "This paper presents an algorithm for labeling curvilinear structure at multiple scales in line drawings and edge images Symbolic CURVE-ELEMENT tokens residing in a spatially-indexed and scale-indexed data structure denote circular arcs fit to image data ."

        (2)Annotation of entities and relations:
        G = {"entities": {"algorithm": {"type": "Generic"}, "labeling curvilinear structure": {"type": "Task"}, "line drawings": {"type": "Material"}, "edge images": {"type": "Material"}, "CURVE-ELEMENT tokens": {"type": "OtherScientificTerm"}, "spatially-indexed and scale-indexed data structure": {"type": "OtherScientificTerm"}, "image data": {"type": "Material"}}, "relations": [["algorithm", "USED-FOR", "labeling curvilinear structure"], ["line drawings", "FEATURE-OF", "labeling curvilinear structure"], ["line drawings", "CONJUNCTION", "edge images"], ["edge images", "FEATURE-OF", "labeling curvilinear structure"], ["CURVE-ELEMENT tokens", "PART-OF", "spatially-indexed and scale-indexed data structure"]]}
        
        (3)The serialized output is:
        [{"span": "algorithm", "type": "Generic", "targets": [{"relation": "USED-FOR", "span": "labeling curvilinear structure", "type": "Task"}]}, {"span": "line drawings", "type": "Material", "targets": [{"relation": "FEATURE-OF", "ref": "labeling curvilinear structure"}, {"relation": "CONJUNCTION", "span": "edge images", "type": "Material", "targets": [{"relation": "FEATURE-OF", "ref": "labeling curvilinear structure"}]}]}, {"span": "CURVE-ELEMENT tokens", "type": "OtherScientificTerm", "targets": [{"relation": "PART-OF", "span": "spatially-indexed and scale-indexed data structure", "type": "OtherScientificTerm"}]}, {"span": "image data", "type": "Material"}]
     
      # 4.Demonstrations of input and output

        (1)Example 1:
        text = "Considering the size , we utilized acoustic vector sensor -LRB- AVS -RRB- and proposed a DOA estimation algorithm previously -LSB- 1 -RSB- , offering high accuracy with larger-than-15dB SNR but is deteriorated by non-speech interferences -LRB- NSI -RRB- ."

        output = [{"span": "acoustic vector sensor -LRB- AVS -RRB-", "type": "Method"}, {"span": "DOA estimation algorithm", "type": "Method"}, {"span": "non-speech interferences -LRB- NSI -RRB-", "type": "OtherScientificTerm"}]

        (2)Example 2:
        text = "CriterionSM Online Essay Evaluation Service includes a capability that labels sentences in student writing with essay-based discourse elements -LRB- e.g. , thesis statements -RRB- ."

        output = [{"span": "CriterionSM Online Essay Evaluation Service", "type": "Task"}, {"span": "essay-based discourse elements", "type": "OtherScientificTerm", "targets": [{"relation": "PART-OF", "ref": "CriterionSM Online Essay Evaluation Service"}]}, {"span": "thesis statements", "type": "OtherScientificTerm", "targets": [{"relation": "HYPONYM-OF", "ref": "essay-based discourse elements"}]}]

        (3) Example 3:
        text = "This system identifies features of sentences based on semantic similarity measures and discourse structure .",

        output = [{"span": "system", "type": "Generic", "targets": [{"relation": "USED-FOR", "span": "features", "type": "OtherScientificTerm"}]}, {"span": "semantic similarity measures", "type": "Metric", "targets": [{"relation": "USED-FOR", "ref": "features"}]}, {"span": "discourse structure", "type": "OtherScientificTerm", "targets": [{"relation": "USED-FOR", "ref": "features"}, {"relation": "CONJUNCTION", "ref": "semantic similarity measures"}]}]

      # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
      # Below is the test sample: 
      '''
  ,

  "ade":'''
      ## 3.2 Serialization Output Example:

      (1)text = "Hypersensitivity to aspirin can be manifested as acute asthma , urticaria and/or angioedema , or a systemic anaphylactoid reaction ."

      (2)Annotation of entities and relations:
      G = {"entities": {"aspirin": {"type": "Drug"}, "urticaria": {"type": "Adverse-Effect"}, "angioedema": {"type": "Adverse-Effect"}, "systemic anaphylactoid reaction": {"type": "Adverse-Effect"}}, "relations": [["urticaria", "adverse-reaction-of", "aspirin"], ["angioedema", "adverse-reaction-of", "aspirin"], ["systemic anaphylactoid reaction", "adverse-reaction-of", "aspirin"]]}

      (3)The serialized output is:
       [{"span": "aspirin", "type": "Drug"}, {"span": "urticaria", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "aspirin"}]}, {"span": "angioedema", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "aspirin"}]}, {"span": "systemic anaphylactoid reaction", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "aspirin"}]}]

    # 4.Demonstrations of input and output

      (1)Example 1:
      text = "The mechanism of anaphylactoid reaction to zomepirac in this case , therefore , remains unclear ."

      output = [{"span": "anaphylactoid reaction", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "span": "zomepirac", "type": "Drug"}]}]

      (2)Example 2:
      text = "CONCLUSIONS : In our reported case , a local hyperproduction of TNF - alpha from macrophages that was induced by the injected insulin could explain the dedifferentiation of the adipocytes of the subcutaneous tissue and the reversion that was induced by the local injection of dexamethasone ."

      output =  [{"span": "hyperproduction of TNF - alpha", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "span": "insulin", "type": "Drug"}]}, {"span": "dedifferentiation of the adipocytes", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "insulin"}]}]

      (3)Example 3:
      text = "During clarithromycin coadministration , four out of the seven patients developed moderate - to - severe toxic symptoms of carbamazepine , such as drowsiness , dizziness , and ataxia , which resolved within 5 days after clarithromycin discontinuation ."

      output =  [{"span": "clarithromycin", "type": "Drug"}, {"span": "toxic symptoms", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "clarithromycin"}, {"relation": "adverse-reaction-of", "span": "carbamazepine", "type": "Drug"}]}, {"span": "drowsiness", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "clarithromycin"}, {"relation": "adverse-reaction-of", "ref": "carbamazepine"}]}, {"span": "dizziness", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "clarithromycin"}, {"relation": "adverse-reaction-of", "ref": "carbamazepine"}]}, {"span": "ataxia", "type": "Adverse-Effect", "targets": [{"relation": "adverse-reaction-of", "ref": "clarithromycin"}, {"relation": "adverse-reaction-of", "ref": "carbamazepine"}]}]

    # **Important**: Please output the test results (string) in serialized format!(**as designated in 3.2, the string after "The serialized output is:"**) do not output any extra content. Ensure the output labels are among the provided entity labels and relation labels! Ensure the output sequence has correct bracket closure and conforms to the format!
      # Below is the test sample: 
  '''
}


DATASET_2_SCHEMA = {
  "ace2005":'''
    Your task is to perform joint entity and relation extraction.

    # 1.Task Schema
    Ensure the output labels are within the given 7 entity labels and 6 relation labels! Do not confuse entity labels and relation labels (do not predict entity types as relation types or relation types as entity types).

    ## 1.1 Entity Labels (7 types)
    (1) PER: 
    Refers to persons, including individuals, roles, titles, pronouns or specific groups, which can be literally full names, given names, surnames, nicknames, etc. Note that personal pronouns should also be labeled as PER. 
    Examples: Mohammad Atrianfar, who, mayor, doctors, everyone.
    (2) ORG: 
    Refers to organizations, including legal entities, companies, government agencies, military units, political parties, sports teams, schools, etc. 
    Examples: AFP (news agency), newspaper, AMA, Congress, Google.
    (3) GPE: 
    Refers to geopolitical entities, namely countries, cities, provinces, states, etc. with clear boundaries and governments. It has both location (LOC) and organization (ORG) attributes. For example, "the United States" in "the U.S. government" is usually labeled as GPE. 
    Examples: Iran, Tehran, Texas, America, Iraq.
    (4) LOC: 
    Refers to locations, usually non-political places and geographic concepts not belonging to GPE, including geographic locations, water bodies, locative adverbs, and pronouns. 
    Examples: downtown, border, world, sub-Saharan, Africa.
    (5) FAC: 
    Refers to man-made facilities or buildings, such as airports, bridges, hospitals, schools, museums, military bases, etc. 
    Examples: hospitals, downtown hotels, base, White House, cafe, airport.
    (6) VEH: 
    Refers to vehicles, physical equipment used to transport people or goods, including cars, airplanes, ships, rockets, helicopters, etc., including pronouns. 
    Examples: flight, van, cockpit, helicopter.
    (7) WEA: 
    Refers to weapons, including firearms, explosives, missiles and other offensive devices. 
    Examples: bomb, knife, artillery, missiles.

    ## 1.2 Relation Labels (6 types)
    (1) ORG-AFF: 
    Refers to organizational affiliation, describing employment, membership or ownership relations between people and organizations, or between organizations. 
    Examples: director (PER) -> newspaper (ORG), Mohammad Atrianfar (PER) -> Hamshahri (ORG), CEO (PER) -> company (ORG), Marines (PER) -> U.S. (GPE), governor (PER) -> Texas (GPE).
    (2) PER-SOC: 
    Refers to social relations, describing personal, family, professional or social connections between two person entities. It is not a self-loop relation. 
    Examples: their (PER) -> friends (PER), baby (PER) -> mother (PER), father (PER) -> his (PER), woman (PER) -> husband (PER), Our (PER) -> colleagues (PER).
    (3) PHYS: 
    Refers to physical location, describing the physical space where an entity is currently located (not affiliation, only physical presence). 
    Examples: I (PER) -> Oklahoma (GPE), Andrew Luster (PER) -> Los Angeles International Airport (FAC), He (PER) -> Charlottesville (GPE), Bush (PER) -> White House (FAC), people (PER) -> cafe (FAC).
    (4) ART: 
    Refers to artifact relation, describing the use or possession of facilities, weapons or vehicles by persons, organizations or GPEs. 
    Examples: McDonald's (ORG) -> restaurant (FAC), your (PER) -> states (GPE).
    (5) GEN-AFF: 
    Refers to general affiliation, describing citizenship, residency, origin and other ties between people/organizations and geographic regions, indicating that an entity belongs to a larger, usually geographic or ethnic group. 
    Examples: newspaper (ORG) -> Iran (GPE), doctors (PER) -> where (GPE, referring to Texas), everybody (PER) -> here (GPE, referring to America), men (PER) -> American (GPE), physician (PER) -> Iraqi (GPE).
    (6) PART-WHOLE: 
    Part-whole relation. Indicates that one entity is a component of another, such as inclusion relations between geographic or organizational units. 
    Examples: boards (ORG) -> state (GPE), Public School of Health (ORG) -> Harvard (ORG), restaurant (FAC) -> Istanbul (GPE), countries (GPE) -> North African (LOC), border (LOC) -> Iraq (GPE).
  ''',

  "conll04":'''
    Your task is to perform joint entity and relation extraction.

    # 1. Task Schema
    Ensure the output labels are within the given 4 entity labels and 5 relation labels! Do not confuse entity labels and relation labels (do not predict entity types as relation types or relation types as entity types).

    ## 1.1 Entity Labels (4 types)
    (1) peop: 
    Person, referring to individuals, groups, and identity-bearing pronouns, literally including names, occupational pronouns, and personal pronouns. It includes politicians, scientists, ordinary individuals, etc.
    Examples: Bruno Pusterla, Oswald, Kennedy, he, members.

    (2) org:
    Organization, including entities such as companies, universities, government agencies, associations, and military forces.
    Examples: Radio Reloj Network, FBI, Secret Service, Assembly, CNN.

    (3) loc:
     Location, including entities such as countries, cities, provinces, and geographic regions.
    Examples: Havana, U.S., Italy, Germany, Middletown.

    (4) other: 
    Other types of entities, including dates, quantities, weights, species, or other entities not belonging to the above three categories.
    Examples: 13 Feb 94, 370, 500 acres, rice, Marxist, 2100 GMT.

    ## 1.2 Relation Labels (5 types): Note that self-loop relations are not allowed in this dataset.
    (1) work_for
    Meaning: Affiliation or employment relation, indicating that a person works for or serves an organization.
    Typical pattern: peop work_for org.
    Examples: Bruno Pusterla → Italian Agricultural Confederation, Oswald → U.S. Marines.

    (2) orgbased_in
    Meaning: Indicates that the headquarters or branch of an organization is located in a certain place.
    Typical pattern: org orgbased_in loc.
    Examples: Radio Reloj Network → Havana, Eaglebrook East → Middletown.

    (3) located_in
    Meaning: A location is situated inside another location.
    Typical pattern: loc located_in loc.
    Examples: Geneva → Switzerland, Brooklyn → New York.

    (4) live_in
    Meaning: A person resides in a certain place.
    Typical pattern: peop live_in loc.
    Examples: Oswald → New Orleans, Ganic → Federation of Bosnia-Herzegovina.

    (5) kill
    Meaning: Homicide relation, usually Person/Organization → Person (agent kills patient), or event-related.
    Typical pattern: peop kill peop.
    Examples: Oswald → Kennedy, killer → victim.
  ''',

  "scierc":'''
    Your task is to perform joint entity and relation extraction.

    # 1. Task Schema
    Ensure the output labels are within the given 6 entity labels and 7 relation labels! Do not confuse entity labels and relation labels (do not predict entity types as relation types or relation types as entity types).

    ## 1.1 Entity Labels (6 types)
    (1) Task: 
    Refers to the application domain or specific problem that a paper aims to solve, including scientific research tasks or problem setups, usually corresponding to the paper title, research direction, or experimental task. Often appears in -ing form or as a noun phrase.
    Examples: robust visual tracking, silent speech enhancement, MT evaluation, Graph unification, word sense disambiguation.
    
    (2) Method: 
    Refers to algorithms, models, systems, components, or specific scientific techniques used to accomplish a task.
    Examples: Interchange Lemma, particle-filter style tracker, Bayesian framework, algorithm, HMM-based TTS system.

    (3) Material: 
    Refers to experimental data, corpora, languages, or physical resources. Includes personal pronouns (e.g., "it" referring to a dataset).
    Examples: English, French, textual corpora, Wallstreet Journal data, NAM and electrolaryngeal speech.

    (4) Metric: 
    Refers to measurement standards, scores, or evaluation criteria used to quantify the performance or quality of models, methods, or results.
    Examples: BLEU, NIST, accuracy, computational cost, macro-average F1 performance.

    (5) Generic: 
    Refers to general terms that cannot be classified into the above specific types but function as referential expressions in the text.
    Examples: method, it, system, approach, baseline system.

    (6) OtherScientificTerm: 
    Refers to other important scientific terms mentioned in the text, such as physical phenomena, features, or attributes, not directly categorized as Task/Method/Material.
    Examples: intrinsic object structure, sound quality, redundant copying, cyclic structures, intensity relations.

    ## 1.2 Relation Labels (7 types)
    Assume that X is the head entity,and Y is the tail entity.
    (1) USED-FOR
    Meaning: X is used to accomplish or realize Y (X is applied to Y).
    Typical pattern: Method/Material USED-FOR Task.
    Examples: method USED-FOR paraphrase, real-time VC USED-FOR speech enhancement systems, DSP USED-FOR real-time VC.

    (2) PART-OF
    Meaning: X is a component or step of Y (part-whole relation).
    Typical pattern: Subtask/Component PART-OF Task/Method/Material.
    Examples: Graph unification PART-OF grammar parsing, speed-up element PART-OF unification algorithms, internal model PART-OF hypothesis network.

    (3) HYPONYM-OF
    Meaning: X is a subordinate category of Y (X is a kind of Y, "is-a" relation).
    Examples: French HYPONYM-OF languages, BLEU HYPONYM-OF evaluation measures, InfoMagnets HYPONYM-OF exploration tool.

    (4) CONJUNCTION (symmetric relation)
    Meaning: X and Y appear coordinately (used jointly, as combined methods/features), with equal status in the text, usually connected by "and/or".
    Typical pattern: "and" relation between two methods or two terms.
    Examples: BLEU CONJUNCTION NIST, nouns CONJUNCTION reflexive pronouns, inference CONJUNCTION learning, compression CONJUNCTION mosaicing.

    (5) FEATURE-OF
    Meaning: X is an attribute or feature of Y (Y possesses feature X).
    Examples: grammatical gender FEATURE-OF languages, computational resources FEATURE-OF devices, joint intensity distribution FEATURE-OF prior knowledge.
    
    (6) EVALUATE-FOR
    Meaning: X is used to evaluate the performance or effectiveness of Y (evaluation relation).
    Typical pattern: Dataset/Benchmark EVALUATE-FOR Method/Model.
    Examples: accuracy EVALUATE-FOR parser, sound quality EVALUATE-FOR NAM, multiple standard datasets EVALUATE-FOR method.

    (7) COMPARE (symmetric relation)
    Meaning: Expresses a comparative relation, where two methods, systems, or models are explicitly compared in performance or properties.
    Examples: tracker COMPARE trackers, approach COMPARE state-of-the-art methods, system COMPARE baseline system.

    ### Conceptual Distinction:
    (1) PART-OF vs. HYPONYM-OF: PART-OF denotes physical or structural inclusion, e.g., (engine, PART-OF, car). HYPONYM-OF denotes logical categorization, e.g., (truck, HYPONYM-OF, car).
    (2) USED-FOR vs. EVALUATE-FOR: USED-FOR emphasizes implementation (A is a tool to achieve B). EVALUATE-FOR emphasizes performance measurement (A is a yardstick to assess B).
    (3) FEATURE-OF vs. PART-OF: FEATURE-OF describes an inherent, non-separable property of an entity. PART-OF describes a separable module or component of an entity.
  ''',

  "ade":'''
    Your task is to perform joint entity and relation extraction.

    # 1. Task Schema
    Ensure output labels only use the provided 2 entity types and 1 relation type! Do not confuse entity labels and relation labels (do not predict entity types as relation types or relation types as entity types).

    ## 1.1 Entity Labels (2 types)
    (1) Drug
    Meaning: Refers to medical drugs, medications, or chemical substances used for treatment, including brand names, generic names, and complex chemical component descriptions.
    Example: imiquimod, nitrofurantoin, acenocoumarol, aspirin, clozapine.

    (2) Adverse-Effect
    Meaning: Refers to adverse reactions, side effects, or negative health impacts caused by drugs, including disease names, physiological symptoms, and even extreme outcomes.
    Example: Eruptive epidermoid cysts, pneumonia, overanticoagulation, acute asthma, died.

    ## 1.2 Relation Label (1 type)
    (1) adverse-reaction-of
    Meaning: Indicates the adverse reaction is caused by the drug. The head entity is the adverse effect, and the tail entity is the drug.
    Example: pneumonia → nitrofurantoin, acute asthma → aspirin, Eosinophilia → clozapine, hypoxemia → imiquimod, died → sweet spirits of nitre.
  '''
}


DATASETS = ["ace2005", "conll04", "scierc", "ade"]
FORMATS = ["dfs", "naive", "sel","dfsjson"]
EXAMPLE_MAP = {
  "dfs": DATASET_2_EXAMPLE_dfs,
  "naive": DATASET_2_EXAMPLE_naive,
  "sel": DATASET_2_EXAMPLE_sel,
  "dfsjson": DATASET_2_EXAMPLE_dfsjson
}

DATASET_2_PROMPT = dict()
for dataset in DATASETS:
  DATASET_2_PROMPT[dataset] = dict()
  for f in FORMATS:
     DATASET_2_PROMPT[dataset][f] = DATASET_2_SCHEMA[dataset] + DATASET_2_FORMAT[f] + EXAMPLE_MAP[f][dataset]

if __name__ == "__main__":
  import sys
  args = sys.argv
  if len(args) != 3:
    print("Usage: python prompt_3shot.py <dataset> <format>")
    sys.exit(1)
  dataset = args[1]
  fmt = args[2]
  print(DATASET_2_PROMPT[dataset][fmt])

