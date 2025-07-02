correspondances_physiques_groupes = correspondances_physiques_groupes = [
    # Groupes existants (inchangés)
    ["Châtelet", "Châtelet Les Halles", "Les Halles"],
    ["Saint-Michel", "Saint-Michel Notre-Dame", "Notre Dame", "Saint Michel Notre Dame"],
    ["Gare de Lyon", "Paris Gare de Lyon"],
    ["Gare d'Austerlitz", "Paris Austerlitz"],
    ["Montparnasse Bienvenüe", "Paris Montparnasse"],
    ["Saint-Lazare", "Paris Saint-Lazare"],
    ["Gare de l'Est", "Paris Est"],
    ["Gare du Nord", "Paris Nord", "Magenta"],
    ["Nation", "Paris Nation"],
    ["Invalides", "Esplanade des Invalides", "Pont Alexandre III Invalides"],
    ["Charles de Gaulle – Étoile", "Charles de Gaulle Etoile", "Etoile"],
    ["La Défense", "La Défense Grande Arche", "Grande Arche de La Défense", "La Défense (Grande Arche)"],
    ["Bibliothèque François Mitterrand", "Bibliotheque Francois Mitterrand", "Bibl. François Mitterrand"],
    ["Denfert-Rochereau", "Paris Denfert-Rochereau"],
    ["Bercy", "Paris Bercy"],
    ["Porte Maillot", "Neuilly Porte Maillot", "Porte Maillot Palais des Congrès"],
    ["Porte de Clichy", "Paris Porte de Clichy"],
    ["Stade de France", "Stade de France – Saint-Denis", "Saint-Denis"],
    ["Champ de Mars", "Champ de Mars Tour Eiffel", "Tour Eiffel"],
    ["Aéroport Charles de Gaulle 1", "CDG 1"],
    ["Aéroport Charles de Gaulle 2 TGV", "CDG 2 TGV", "Aéroport Charles de Gaulle 2"],
    ["Marne-la-Vallée Chessy", "Marne la Vallée Chessy", "Chessy Marne-la-Vallée", "Disneyland Paris"],
    ["Val de Fontenay", "Fontenay-sous-Bois"],
    ["Bourg-la-Reine", "Bourg la Reine"],
    ["Juvisy", "Juvisy sur Orge"],
    ["Massy Palaiseau", "Massy-Palaiseau"],
    ["Versailles Chantiers", "Versailles-Chantiers"],
    ["Versailles Rive Gauche", "Versailles Château Rive Gauche"],
    ["Versailles Château Rive Gauche", "Versailles Rive Gauche", "Versailles Château", "Château de Versailles"],
    ["Sceaux", "Parc de Sceaux"],
    ["Clamart", "Issy-Val de Seine"],
    ["Vincennes", "Château de Vincennes", "Chateau de Vincennes"],
    ["Notre-Dame-des-Champs", "Notre Dame des Champs"],
    ["Pont de Sèvres", "Pont de Sevres"],
    ["Aéroport d'Orly", "Aéroport Orly"],
    ["Massy", "Massy Palaiseau", "Massy-Palaiseau"],
    ["Bibliothèque François Mitterrand", "Bibl. François Mitterrand"],

    # -------- Ajouts pour monuments du dataset --------
    # Tour Eiffel
    ["Tour Eiffel", "Eiffel Tower", "Champ de Mars Tour Eiffel", "Champ de Mars", "Tour-Eiffel"],
    # Arc de Triomphe
    ["Arc de Triomphe", "Charles de Gaulle – Étoile", "Charles de Gaulle Etoile", "Place de l'Étoile"],
    # Louvre
    ["Louvre", "Musée du Louvre", "Pyramide du Louvre", "Louvre Museum"],
    # Musée d'Orsay
    ["Musée d'Orsay", "Gare d'Orsay", "Orsay Museum"],
    # Sacré-Cœur
    ["Sacré-Cœur", "Basilique du Sacré-Cœur", "Montmartre", "Basilique de Montmartre"],
    # Notre-Dame de Paris
    ["Notre-Dame de Paris", "Cathédrale Notre-Dame", "Notre Dame"],
    # Panthéon
    ["Panthéon", "Le Panthéon", "Panthéon Paris"],
    # Opéra Garnier
    ["Opéra Garnier", "Palais Garnier", "Opéra de Paris"],
    # Jardin du Luxembourg
    ["Jardin du Luxembourg", "Luxembourg", "Parc du Luxembourg"],
    # Jardin des Plantes
    ["Jardin des Plantes", "Muséum national d'Histoire naturelle", "MNHN", "Jardin des Plantes Paris"],
    # Place de la Concorde
    ["Place de la Concorde", "Concorde"],
    # Hôtel des Invalides
    ["Hôtel des Invalides", "Invalides", "Musée de l'Armée", "Dôme des Invalides"],
    # Place Vendôme
    ["Place Vendôme", "Vendôme"],
    # Palais Royal
    ["Palais Royal", "Palais-Royal Musée du Louvre", "Palais Royal - Musée du Louvre"],
    # Centre Pompidou
    ["Centre Pompidou", "Beaubourg", "Musée National d'Art Moderne"],
    # Grande Arche de la Défense
    ["Grande Arche de la Défense", "La Défense", "La Défense Grande Arche"],

    # -------- Exemples d'autres gares/hubs --------
    ["Saint-Germain-en-Laye", "Saint-Germain-en-Laye Château", "Saint Germain en Laye"],
    ["Rueil-Malmaison", "Rueil Malmaison"],
    ["Sèvres", "Pont de Sèvres", "Sevres"],
    ["Fontainebleau", "Fontainebleau Avon"],
    ["Bois de Vincennes", "Vincennes", "Château de Vincennes"],

]


# Profils d'affluence par jour (adapté à la réalité des transports)
PROFILE_JOUR = {
    'lundi': 1.0,
    'mardi': 0.95,
    'mercredi': 0.9,
    'jeudi': 0.95,
    'vendredi': 1.0,
    'samedi': 0.8,
    'dimanche': 0.6
}

# Profils d'affluence par heure (adapté à l'horaire métro/rer)
PROFILE_HEURE = {
    6: 0.3,
    7: 0.7,
    8: 1.0,
    9: 0.8,
    10: 0.5,
    11: 0.4,
    12: 0.5,
    13: 0.6,
    14: 0.6,
    15: 0.7,
    16: 0.8,
    17: 1.0,
    18: 1.0,
    19: 0.8,
    20: 0.5,
    21: 0.3,
    22: 0.2,
    23: 0.1,
    0: 0.05,
    1: 0.01,
    2: 0.01,
    3: 0.01,
    4: 0.01,
    5: 0.05
}

BIG_HUBS_SCORE = {
    "gare du nord": 1.0,                     
    "gare de lyon": 0.98,
    "saint lazare": 0.96,
    "gare de l'est": 0.85,
    "montparnasse bienvenue": 0.87,
    "chatelet": 0.95,
    "la defense": 0.90,
    "republique": 0.85,
    "nation": 0.82,
    "denfert rochereau colonel rol tanguy": 0.75,
    "hotel de ville": 0.75,
    "opera": 0.73,
    "invalides": 0.7,
    "bastille": 0.65,
    "charles de gaulle etoile": 0.82,
    "bibliotheque francois mitterrand": 0.7,
    "place d'italie": 0.65,
    "massy": 0.6,
    "aubervilliers pantin quatre chemins": 0.6,
}


LINE_SCORE = {
    "RER A": 1.00,     
    "RER B": 0.9,       
    "RER D": 0.8,       
    "RER C": 0.7,
    "RER E": 0.6,

    "METRO 1": 1.00,    
    "METRO 4": 1.00,    
    "METRO 9": 0.9,     
    "METRO 7": 0.85,
    "METRO 13": 0.8,
    "METRO 14": 0.8,    
    "METRO 8": 0.75,
    "METRO 5": 0.7,
    "METRO 6": 0.7,
    "METRO 2": 0.7,
    "METRO 3": 0.65,
    "METRO 12": 0.65,
    "METRO 10": 0.5,    
    "METRO 11": 0.5,
}

DEFAULT_LINE_SCORE = 0.6  
