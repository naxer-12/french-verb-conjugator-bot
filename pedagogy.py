"""
Pedagogical French Language Module.
Provides bilingual (French & English) explanations, verb classifications,
mnemonic tips, synonyms, and contextual example sentences designed for French learners.
"""

from typing import Dict, List, Any, Optional
import html
import re

# ---------------------------------------------------------------------------
# Bilingual Mood & Tense Educational Guides
# ---------------------------------------------------------------------------

MOOD_GUIDES: Dict[str, Dict[str, str]] = {
    "Indicatif": {
        "fr": "Exprime des faits réels, certains, objectifs et concrets dans le présent, le passé ou le futur.",
        "en": "Expresses real, objective facts, certainties, and habits in the present, past, or future.",
        "badge": "Factual & Objective / Réel & Factuel",
    },
    "Conditionnel": {
        "fr": "Exprime un souhait, une hypothèse, une possibilité ou une demande polie ('voudrais', 'pourrais').",
        "en": "Used for hypothetical situations, polite requests ('would / could'), and conditional outcomes.",
        "badge": "Hypothetical & Politeness / Hypothèse & Politesse",
    },
    "Subjonctif": {
        "fr": "Exprime le doute, l'émotion, le souhait ou la nécessité après des structures comme 'il faut que' ou 'bien que'.",
        "en": "Used for feelings, doubts, wishes, and necessity (typically triggered by 'il faut que...').",
        "badge": "Subjectivity & Necessity / Doute & Nécessité",
    },
    "Impératif": {
        "fr": "Exprime un ordre, une instruction, un conseil ou une interdiction directe sans sujet exprimé.",
        "en": "Used for direct commands, instructions, advice, and invitations without an explicit subject pronoun.",
        "badge": "Commands & Advice / Ordres & Conseils",
    },
}

TENSE_GUIDES: Dict[str, Dict[str, str]] = {
    "Présent": {
        "fr": "Actions actuelles, vérités générales ou habitudes.",
        "en": "Current actions, habits, and universal truths.",
    },
    "Imparfait": {
        "fr": "Descriptions passées, habitudes et actions continues ('faisait', 'était').",
        "en": "Past descriptions, habits, and ongoing background actions ('used to' / 'was doing').",
    },
    "Passé composé": {
        "fr": "Événements ponctuels et complétés dans le passé avec résultat présent.",
        "en": "Specific completed past events with defined timeframes ('did' / 'have done').",
    },
    "Passé simple": {
        "fr": "Temps littéraire et historique pour narrer des actions passées ponctuelles.",
        "en": "Formal literary past used in literature, news, and formal history.",
    },
    "Plus-que-parfait": {
        "fr": "Action passée qui s'est déroulée avant une autre action passée ('j'avais fait').",
        "en": "Past action that happened before another past event ('had done').",
    },
    "Passé antérieur": {
        "fr": "Temps littéraire exprimant une antériorité immédiate ('dès qu'il eut fini').",
        "en": "Literary past expressing an action completed just before another past action.",
    },
    "Futur simple": {
        "fr": "Actions futures, prévisions et promesses ('je ferai', 'nous irons').",
        "en": "Future plans, predictions, and definite promises ('will do').",
    },
    "Futur antérieur": {
        "fr": "Action future qui sera terminée avant une autre action future ('j'aurai fini').",
        "en": "Future action that will have been completed before another point in time ('will have done').",
    },
    "Passé 1re forme": {
        "fr": "Action qui aurait pu se réaliser dans le passé sous condition ('j'aurais aimé').",
        "en": "Past condition that would have occurred under certain circumstances ('would have done').",
    },
    "Passé 2e forme": {
        "fr": "Forme littéraire et soutenue du conditionnel passé ('j'eusse aimé').",
        "en": "Archaic/literary formal past conditional ('would have').",
    },
    "Passé": {
        "fr": "Forme composée exprimant une action antérieure complétée.",
        "en": "Compound form expressing a completed prior action.",
    },
}


# ---------------------------------------------------------------------------
# Curated High-Frequency French Verbs Knowledge Base
# ---------------------------------------------------------------------------

CURATED_VERBS: Dict[str, Dict[str, Any]] = {
    "être": {
        "meaning_en": "To be",
        "meaning_fr": "Exister, se trouver dans un état ou un lieu",
        "group": "Auxiliaire / 3ème groupe (irrégulier)",
        "level": "A1 (Essentiel)",
        "auxiliaire": "avoir (pour former les temps composés d'être : j'ai été)",
        "tip_en": "Essential auxiliary verb. The stem changes completely across tenses (Présent: suis/es/est, Imparfait: ét-, Futur: ser-). Used to conjugate reflexive verbs and verbs of movement.",
        "tip_fr": "Verbe auxiliaire indispensable. Le radical change selon les temps (suis, étais, serai). Sert d'auxiliaire pour tous les verbes pronominaux et les verbes de la 'maison d'être'.",
        "synonyms": [
            ("exister", "to exist"),
            ("se trouver", "to be located / to happen to be"),
            ("constituer", "to constitute / make up"),
            ("demeurer", "to remain / stay"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Je suis très heureux d'apprendre le français.",
                "en": "I am very happy to learn French.",
            },
            {
                "tense": "Passé composé",
                "fr": "Hier, elle a été surprise par la bonne nouvelle.",
                "en": "Yesterday, she was surprised by the good news.",
            },
            {
                "tense": "Futur simple",
                "fr": "Demain, nous serons prêts pour l'examen.",
                "en": "Tomorrow, we will be ready for the exam.",
            },
        ],
    },
    "avoir": {
        "meaning_en": "To have",
        "meaning_fr": "Posséder, disposer de, éprouver une sensation",
        "group": "Auxiliaire / 3ème groupe (irrégulier)",
        "level": "A1 (Essentiel)",
        "auxiliaire": "avoir (j'ai eu)",
        "tip_en": "Primary auxiliary verb used for 90%+ of French verbs in compound tenses. Also used in classic French idioms for age and physical states: 'avoir 20 ans' (to be 20), 'avoir faim' (to be hungry), 'avoir soif' (to be thirsty).",
        "tip_fr": "Auxiliaire majeur pour plus de 90 % des verbes aux temps composés. Utilisé pour l'âge et les sensations corporelles : 'avoir faim', 'avoir froid', 'avoir 25 ans'.",
        "synonyms": [
            ("posséder", "to own / possess"),
            ("détenir", "to hold / possess"),
            ("disposer de", "to have at one's disposal"),
            ("bénéficier de", "to enjoy / benefit from"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "J'ai un livre intéressant sur la grammaire française.",
                "en": "I have an interesting book on French grammar.",
            },
            {
                "tense": "Imparfait",
                "fr": "Quand nous étions jeunes, nous avions beaucoup d'énergie.",
                "en": "When we were young, we had a lot of energy.",
            },
            {
                "tense": "Conditionnel Présent",
                "fr": "Si j'avais du temps, j'aurais plus de loisirs.",
                "en": "If I had time, I would have more hobbies.",
            },
        ],
    },
    "parler": {
        "meaning_en": "To speak, to talk",
        "meaning_fr": "Exprimer sa pensée par la parole, s'exprimer",
        "group": "1er groupe (verbe régulier en -er)",
        "level": "A1 (Débutant)",
        "auxiliaire": "avoir (j'ai parlé)",
        "tip_en": "The quintessential regular 1st-group verb. Present endings: -e, -es, -e, -ons, -ez, -ent. Notice that -e, -es, and -ent are completely silent! Only pronounce the stem [paʁl].",
        "tip_fr": "Modèle par excellence du 1er groupe (-er). Les terminaisons au présent sont -e, -es, -e, -ons, -ez, -ent. Attention : les terminaisons -e, -es, -ent sont muettes !",
        "synonyms": [
            ("discuter", "to discuss / to chat"),
            ("s'entretenir", "to converse / to talk with"),
            ("bavarder", "to chat / to chatter informally"),
            ("dialoguer", "to engage in a dialogue"),
            ("s'exprimer", "to express oneself"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Je parle français avec mes camarades de classe.",
                "en": "I speak French with my classmates.",
            },
            {
                "tense": "Passé composé",
                "fr": "Nous avons parlé de notre prochain voyage à Paris.",
                "en": "We talked about our next trip to Paris.",
            },
            {
                "tense": "Futur simple",
                "fr": "Bientôt, vous parlerez avec une grande fluidité.",
                "en": "Soon, you will speak with great fluency.",
            },
        ],
    },
    "aller": {
        "meaning_en": "To go",
        "meaning_fr": "Se déplacer d'un lieu à un autre",
        "group": "3ème groupe (irrégulier malgré la finale en -er)",
        "level": "A1 (Essentiel)",
        "auxiliaire": "être (je suis allé / allée)",
        "tip_en": "Irregular 3rd group verb. Used with an infinitive to form the 'Futur Proche' (near future): 'Je vais manger' (I am going to eat). Takes 'être' in compound tenses: 'Je suis allé(e)'.",
        "tip_fr": "Verbe très irrégulier. Sert de semi-auxiliaire pour le Futur Proche : 'aller + infinitif' (je vais partir). Prend obligatoirement l'auxiliaire 'être' au passé composé.",
        "synonyms": [
            ("se rendre", "to make one's way to / to head to"),
            ("marcher", "to walk"),
            ("partir", "to leave / head out"),
            ("circuler", "to move around / circulate"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Je vais au musée du Louvre ce matin.",
                "en": "I am going to the Louvre museum this morning.",
            },
            {
                "tense": "Passé composé",
                "fr": "Hier, elle est allée à la bibliothèque.",
                "en": "Yesterday, she went to the library.",
            },
            {
                "tense": "Futur simple",
                "fr": "L'été prochain, nous irons en France.",
                "en": "Next summer, we will go to France.",
            },
        ],
    },
    "faire": {
        "meaning_en": "To do, to make",
        "meaning_fr": "Accomplir une action, fabriquer, réaliser",
        "group": "3ème groupe (irrégulier)",
        "level": "A1 (Essentiel)",
        "auxiliaire": "avoir (j'ai fait)",
        "tip_en": "Highly versatile verb. Used for weather ('Il fait beau' = the weather is nice), chores ('faire la vaisselle' = do the dishes), and activities ('faire du sport' = play sports). Remember 'vous faites' and 'ils font' in the present!",
        "tip_fr": "Verbe polyvalent utilisé pour la météo ('il fait froid'), le sport ('faire du vélo') et les activités. Attention aux formes au présent : 'vous faites' et 'ils font'.",
        "synonyms": [
            ("réaliser", "to carry out / accomplish"),
            ("accomplir", "to achieve / fulfill"),
            ("créer", "to create / invent"),
            ("fabriquer", "to manufacture / make"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Qu'est-ce que vous faites ce week-end ?",
                "en": "What are you doing this weekend?",
            },
            {
                "tense": "Passé composé",
                "fr": "J'ai fait tous mes devoirs de français.",
                "en": "I did all my French homework.",
            },
            {
                "tense": "Subjonctif Présent",
                "fr": "Il faut que tu fasses attention à la prononciation.",
                "en": "You must pay attention to pronunciation.",
            },
        ],
    },
    "pouvoir": {
        "meaning_en": "To be able to, can, may",
        "meaning_fr": "Avoir la capacité ou la permission de faire quelque chose",
        "group": "3ème groupe (modal irrégulier)",
        "level": "A1-A2 (Modal)",
        "auxiliaire": "avoir (j'ai pu)",
        "tip_en": "Modal verb expressing ability or permission. In the conditional, 'pourriez-vous' is the standard polite formula for 'could you'. Present: je peux (or formal 'je puis'), tu peux, il peut, nous pouvons, vous pouvez, ils peuvent.",
        "tip_fr": "Verbe modal de capacité ou permission. Au conditionnel ('pourriez-vous...'), c'est la formule polie par excellence. Au subjonctif : 'que je puisse'.",
        "synonyms": [
            ("être capable de", "to be capable of"),
            ("avoir la possibilité de", "to have the possibility to"),
            ("être autorisé à", "to be allowed to"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Est-ce que je peux vous poser une question ?",
                "en": "Can I ask you a question?",
            },
            {
                "tense": "Conditionnel Présent",
                "fr": "Pourriez-vous répéter plus lentement, s'il vous plaît ?",
                "en": "Could you please repeat more slowly?",
            },
            {
                "tense": "Passé composé",
                "fr": "Nous avons pu réserver les billets à temps.",
                "en": "We were able to book the tickets in time.",
            },
        ],
    },
    "vouloir": {
        "meaning_en": "To want, to wish",
        "meaning_fr": "Avoir le désir, la volonté de quelque chose",
        "group": "3ème groupe (modal irrégulier)",
        "level": "A1-A2 (Modal)",
        "auxiliaire": "avoir (j'ai voulu)",
        "tip_en": "Expresses desire or intention. Politeness tip: Avoid 'je veux' in restaurants or shops; always use the polite conditional 'je voudrais' ('I would like').",
        "tip_fr": "Exprime le désir. Règle de politesse : au restaurant ou dans les magasins, préférez toujours le conditionnel 'je voudrais' plutôt que 'je veux' qui sonne trop autoritaire.",
        "synonyms": [
            ("désirer", "to desire / wish for"),
            ("souhaiter", "to wish / hope"),
            ("aspirer à", "to aspire to"),
            ("envisager", "to contemplate / plan to"),
        ],
        "examples": [
            {
                "tense": "Conditionnel Présent",
                "fr": "Je voudrais un café et un croissant, s'il vous plaît.",
                "en": "I would like a coffee and a croissant, please.",
            },
            {
                "tense": "Présent",
                "fr": "Ils veulent voyager autour du monde.",
                "en": "They want to travel around the world.",
            },
            {
                "tense": "Subjonctif Présent",
                "fr": "Le professeur veut que nous réussissions tous.",
                "en": "The teacher wants us all to succeed.",
            },
        ],
    },
    "savoir": {
        "meaning_en": "To know (facts, how to do something)",
        "meaning_fr": "Avoir la connaissance de faits, savoir comment faire",
        "group": "3ème groupe (irrégulier)",
        "level": "A2",
        "auxiliaire": "avoir (j'ai su)",
        "tip_en": "Distinction with 'connaître': Use 'savoir' for facts, clauses ('Je sais que...'), or learned skills + infinitive ('Je sais nager' = I know how to swim). Use 'connaître' for people and places.",
        "tip_fr": "Différence avec 'connaître' : 'savoir' s'utilise pour des faits, des propositions ('je sais que...') ou des compétences ('je sais nager'). 'Connaître' s'utilise pour des personnes ou des lieux.",
        "synonyms": [
            ("connaître", "to be familiar with (people/places)"),
            ("ignorer", "[Antonyme] to not know / to ignore"),
            ("maîtriser", "to master / command"),
            ("être au courant", "to be informed / in the know"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Savez-vous où se trouve la gare centrale ?",
                "en": "Do you know where the central station is located?",
            },
            {
                "tense": "Imparfait",
                "fr": "Je savais déjà parler deux langues à dix ans.",
                "en": "I already knew how to speak two languages at age ten.",
            },
            {
                "tense": "Subjonctif Présent",
                "fr": "Il est important que vous sachiez cette règle.",
                "en": "It is important that you know this rule.",
            },
        ],
    },
    "prendre": {
        "meaning_en": "To take, to have (food/drink)",
        "meaning_fr": "Saisir, consommer un aliment, monter dans un transport",
        "group": "3ème groupe (famille de -prendre)",
        "level": "A1-A2",
        "auxiliaire": "avoir (j'ai pris)",
        "tip_en": "Verbs ending in '-prendre' (apprendre, comprendre, surprendre) all follow this exact conjugation pattern: Participle is 'pris', plural present doubles the 'n' in 'ils prennent'.",
        "tip_fr": "Tous les verbes de la famille (apprendre, comprendre, reprendre) se conjuguent sur ce modèle. Le participe passé est 'pris', et le 'n' double à la 3e personne du pluriel (ils prennent).",
        "synonyms": [
            ("saisir", "to grab / seize"),
            ("consommer", "to consume / eat / drink"),
            ("attraper", "to catch (transportation/object)"),
            ("adopter", "to adopt / take up"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Je prends le métro chaque matin pour aller au travail.",
                "en": "I take the subway every morning to go to work.",
            },
            {
                "tense": "Passé composé",
                "fr": "Elle a pris une tasse de thé vert après le déjeuner.",
                "en": "She had a cup of green tea after lunch.",
            },
            {
                "tense": "Impératif",
                "fr": "Prenez votre temps pour lire la consigne.",
                "en": "Take your time to read the instructions.",
            },
        ],
    },
    "venir": {
        "meaning_en": "To come",
        "meaning_fr": "Se déplacer vers le lieu où se trouve celui qui parle",
        "group": "3ème groupe (famille de -venir)",
        "level": "A1-A2",
        "auxiliaire": "être (je suis venu / venue)",
        "tip_en": "Takes 'être' in compound tenses. Used with 'de + infinitive' for the 'Passé Récent' (recent past): 'Je viens de finir' = 'I have just finished'.",
        "tip_fr": "Prend l'auxiliaire 'être' au passé composé. Associé à 'de + infinitif', il forme le Passé Récent : 'je viens d'arriver' (action terminée il y a quelques instants).",
        "synonyms": [
            ("arriver", "to arrive / get there"),
            ("parvenir", "to reach / attain"),
            ("accourir", "to rush / run towards"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Est-ce que tu viens à la fête ce soir ?",
                "en": "Are you coming to the party tonight?",
            },
            {
                "tense": "Passé composé",
                "fr": "Ils sont venus nous rendre visite dimanche dernier.",
                "en": "They came to visit us last Sunday.",
            },
            {
                "tense": "Futur simple",
                "fr": "Mon ami viendra me chercher à l'aéroport.",
                "en": "My friend will come pick me up at the airport.",
            },
        ],
    },
    "devoir": {
        "meaning_en": "To have to, must, to owe",
        "meaning_fr": "Avoir l'obligation morale ou matérielle de faire quelque chose",
        "group": "3ème groupe (modal irrégulier)",
        "level": "A2",
        "auxiliaire": "avoir (j'ai dû - note the circumflex accent)",
        "tip_en": "Modal of obligation ('must / have to') and probability ('must be'). In the conditional, 'tu devrais' means 'you should'. Note the circumflex accent on masculine past participle 'dû' to distinguish from article 'du'.",
        "tip_fr": "Verbe d'obligation ou de probabilité. Au conditionnel ('tu devrais'), il exprime le conseil ('you should'). Attention à l'accent circonflexe sur le participe passé masculin 'dû'.",
        "synonyms": [
            ("être obligé de", "to be obliged to"),
            ("falloir", "to be necessary (impersonal)"),
            ("être tenu de", "to be required to"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Nous devons terminer ce travail avant midi.",
                "en": "We must finish this work before noon.",
            },
            {
                "tense": "Conditionnel Présent",
                "fr": "Tu devrais réviser tes verbes irréguliers chaque jour.",
                "en": "You should review your irregular verbs every day.",
            },
            {
                "tense": "Passé composé",
                "fr": "Il a dû partir précipitamment à cause d'une urgence.",
                "en": "He had to leave in a hurry due to an emergency.",
            },
        ],
    },
    "se lever": {
        "meaning_en": "To get up, to stand up",
        "meaning_fr": "Quitter la position couchée ou assise",
        "group": "1er groupe (verbe pronominal / réflexif)",
        "level": "A1-A2",
        "auxiliaire": "être (toujours avec les verbes pronominaux : je me suis levé / levée)",
        "tip_en": "Reflexive verb with stem change: silent 'e' becomes 'è' before silent endings (je me lève, tu te lèves, il se lève, ils se lèvent). All reflexive verbs use 'être' in compound tenses!",
        "tip_fr": "Verbe pronominal avec alternance orthographique : le 'e' devient 'è' devant une syllabe muette (je me lève). Tous les verbes pronominaux prennent l'auxiliaire 'être' !",
        "synonyms": [
            ("se réveiller", "to wake up"),
            ("se mettre debout", "to stand up"),
            ("se dresser", "to rise / stand straight"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Je me lève tous les matins à sept heures.",
                "en": "I get up every morning at seven o'clock.",
            },
            {
                "tense": "Passé composé",
                "fr": "Ce matin, elle s'est levée plus tôt pour faire du sport.",
                "en": "This morning, she got up earlier to work out.",
            },
            {
                "tense": "Futur simple",
                "fr": "Demain, nous nous lèverons à l'aube.",
                "en": "Tomorrow, we will get up at dawn.",
            },
        ],
    },
    "s'appeler": {
        "meaning_en": "To be named, to be called",
        "meaning_fr": "Avoir pour nom, porter le prénom de",
        "group": "1er groupe (pronominal, double consonne en -eler)",
        "level": "A1 (Débutant)",
        "auxiliaire": "être (je me suis appelé / appelée)",
        "tip_en": "Stem alternation in -eler: doubles the 'l' to 'll' before silent endings (je m'appelle, tu t'appelles, il s'appelle, ils s'appellent), but single 'l' for nous/vous (nous nous appelons, vous vous appelez).",
        "tip_fr": "Alternance de consonne : le 'l' double en 'll' devant une terminaison muette (je m'appelle, ils s'appellent), mais reste simple avec nous et vous (nous nous appelons).",
        "synonyms": [
            ("se nommer", "to be named"),
            ("avoir pour nom", "to have as a name"),
            ("être désigné comme", "to be designated as"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Bonjour ! Je m'appelle Julien et j'habite à Lyon.",
                "en": "Hello! My name is Julien and I live in Lyon.",
            },
            {
                "tense": "Présent",
                "fr": "Comment vous vous appelez ?",
                "en": "What is your name? (formal / plural)",
            },
            {
                "tense": "Imparfait",
                "fr": "Autrefois, cette rue s'appelait la rue des Fleurs.",
                "en": "In the past, this street was called Flowers Street.",
            },
        ],
    },
    "comprendre": {
        "meaning_en": "To understand, to include",
        "meaning_fr": "Saisir le sens de quelque chose, contenir en soi",
        "group": "3ème groupe (famille de prendre)",
        "level": "A1-A2",
        "auxiliaire": "avoir (j'ai compris)",
        "tip_en": "Follows the exact same pattern as 'prendre'. The past participle is 'compris'. Present plural: 'nous comprenons', 'vous comprenez', 'ils comprennent' (double 'n').",
        "tip_fr": "Se conjugue exactement comme 'prendre'. Participe passé en -is ('compris'). Double 'n' à la troisième personne du pluriel : 'ils comprennent'.",
        "synonyms": [
            ("saisir", "to grasp / comprehend"),
            ("assimiler", "to assimilate / absorb"),
            ("englober", "to encompass / include"),
            ("concevoir", "to conceive / understand"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Je comprends très bien quand vous parlez calmement.",
                "en": "I understand very well when you speak calmly.",
            },
            {
                "tense": "Passé composé",
                "fr": "Avez-vous compris l'explication du professeur ?",
                "en": "Did you understand the teacher's explanation?",
            },
            {
                "tense": "Conditionnel Présent",
                "fr": "Avec plus d'exemples, tout le monde comprendrait facilement.",
                "en": "With more examples, everyone would understand easily.",
            },
        ],
    },
    "finir": {
        "meaning_en": "To finish, to end",
        "meaning_fr": "Arriver au terme d'une action, achever",
        "group": "2ème groupe (régulier en -ir, participe en -issant)",
        "level": "A1-A2",
        "auxiliaire": "avoir (j'ai fini)",
        "tip_en": "Model verb for the regular 2nd group. Key feature: the stem inserts '-iss-' in all plural forms (nous finissons, vous finissez, ils finissent) and the entire imparfait (je finissais).",
        "tip_fr": "Modèle type du 2ème groupe (-ir). Sa caractéristique essentielle est l'apparition de l'infixe '-iss-' aux personnes du pluriel (nous finissons) et à tout l'imparfait (je finissais).",
        "synonyms": [
            ("achever", "to complete / conclude"),
            ("terminer", "to finish / wrap up"),
            ("clore", "to close / bring to an end"),
            ("aboutir", "to culminate / lead to"),
        ],
        "examples": [
            {
                "tense": "Présent",
                "fr": "Nous finissons notre cours à dix-sept heures.",
                "en": "We finish our class at 5 PM.",
            },
            {
                "tense": "Passé composé",
                "fr": "J'ai fini de lire ce roman passionnant.",
                "en": "I finished reading this thrilling novel.",
            },
            {
                "tense": "Futur simple",
                "fr": "Vous finirez ce projet avant la fin du mois.",
                "en": "You will finish this project before the end of the month.",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Dynamic Morphological Analysis & Rule Synthesizer for Any Verb
# ---------------------------------------------------------------------------

def infer_verb_group(verb: str) -> Dict[str, str]:
    """
    Infers grammatical classification, auxiliary, and student tips based on verb morphology.
    """
    v = verb.lower().strip()
    is_reflexive = v.startswith("se ") or v.startswith("s'")

    if is_reflexive:
        base = v[3:] if v.startswith("se ") else v[2:]
    else:
        base = v

    if base.endswith("er") and base != "aller":
        group_fr = "1er groupe (verbe régulier en -er)"
        group_en = "1st Group (regular -er verb)"
        aux = "être" if is_reflexive else "avoir"
        tip_fr = "Verbe régulier en -er. Terminaisons du présent : -e, -es, -e, -ons, -ez, -ent (les trois du singulier et la 3e du pluriel sont muettes)."
        tip_en = "Regular 1st group verb. Present endings: -e, -es, -e, -ons, -ez, -ent (endings -e, -es, and -ent are completely silent)."
    elif base.endswith("ir"):
        # Most common -ir verbs without -iss- are 3rd group; general assumption:
        group_fr = "2ème ou 3ème groupe en -ir"
        group_en = "2nd or 3rd Group (-ir verb)"
        aux = "être" if is_reflexive else "avoir"
        tip_fr = "Si le participe présent est en '-issant', il s'agit du 2ème groupe (ex: finir -> finissant). Sinon, c'est un verbe irrégulier du 3ème groupe (ex: partir -> partant)."
        tip_en = "If the present participle ends in '-issant', it is a regular 2nd group verb (like finir). Otherwise, it belongs to the irregular 3rd group (like partir)."
    elif base.endswith("re"):
        group_fr = "3ème groupe (verbe en -re)"
        group_en = "3rd Group (-re verb)"
        aux = "être" if is_reflexive else "avoir"
        tip_fr = "Verbe du 3ème groupe. Surveillez le radical qui peut se modifier selon les personnes et les temps."
        tip_en = "3rd group verb with irregular stem changes across tenses."
    elif base.endswith("oir"):
        group_fr = "3ème groupe (verbe en -oir)"
        group_en = "3rd Group (-oir verb)"
        aux = "avoir"
        tip_fr = "Verbe très souvent irrégulier du 3ème groupe avec modifications de radical (ex: vouloir, pouvoir, devoir)."
        tip_en = "Irregular 3rd group verb typically exhibiting major stem modifications (e.g. vouloir, pouvoir, devoir)."
    else:
        group_fr = "Verbe du 3ème groupe"
        group_en = "3rd Group verb"
        aux = "être" if is_reflexive else "avoir"
        tip_fr = "Verbe français nécessitant une attention particulière pour ses terminaisons."
        tip_en = "French verb requiring careful attention to irregular stem variations."

    if is_reflexive:
        tip_fr += " Comme tous les verbes pronominaux, l'auxiliaire aux temps composés est toujours ÊTRE."
        tip_en += " All reflexive verbs conjugate with the auxiliary ÊTRE in compound tenses."

    return {
        "group_fr": group_fr,
        "group_en": group_en,
        "auxiliaire": aux,
        "tip_fr": tip_fr,
        "tip_en": tip_en,
        "is_reflexive": is_reflexive,
    }


def get_verb_study_data(verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Retrieves rich pedagogical study data for a given verb.
    Combines curated knowledge base entries with dynamic morphological analysis.
    """
    canonical = verb.lower().strip()
    if canonical in CURATED_VERBS:
        data = CURATED_VERBS[canonical].copy()
        data["verb"] = canonical
        return data

    # Check without reflexive prefix or with standard normalization
    morph = infer_verb_group(canonical)
    aux = morph["auxiliaire"]
    if conjugation_data and conjugation_data.get("auxiliaire"):
        aux = conjugation_data.get("auxiliaire")

    clean_verb = canonical
    base_name = clean_verb.replace("se ", "").replace("s'", "")
    meaning_en = f"To {base_name}"
    meaning_fr = f"Action d'accomplir le verbe {clean_verb}"

    return {
        "verb": canonical,
        "meaning_en": meaning_en,
        "meaning_fr": meaning_fr,
        "group": morph["group_fr"],
        "level": "Pratique générale / General Practice",
        "auxiliaire": aux,
        "tip_en": morph["tip_en"],
        "tip_fr": morph["tip_fr"],
        "synonyms": [],
        "examples": [
            {
                "tense": "Présent",
                "fr": f"En classe, nous apprenons à bien utiliser '{canonical}'.",
                "en": f"In class, we learn how to properly use '{canonical}'.",
            },
            {
                "tense": "Passé composé",
                "fr": f"L'élève a correctement conjugué le verbe '{canonical}'.",
                "en": f"The student correctly conjugated the verb '{canonical}'.",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Beautiful Telegram Formatting Engines
# ---------------------------------------------------------------------------

def format_student_study_card(verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a high-aesthetic, bilingual pedagogical Study Guide Card for students.
    """
    study = get_verb_study_data(verb, conjugation_data)
    verb_display = html.escape(verb.upper(), quote=False)
    meaning_en = html.escape(study.get("meaning_en", "To speak / do"), quote=False)
    meaning_fr = html.escape(study.get("meaning_fr", ""), quote=False)
    group = html.escape(study.get("group", ""), quote=False)
    level = html.escape(study.get("level", "A1-B2"), quote=False)
    aux = html.escape(study.get("auxiliaire", "avoir / être"), quote=False)
    tip_en = html.escape(study.get("tip_en", ""), quote=False)
    tip_fr = html.escape(study.get("tip_fr", ""), quote=False)

    lines = [
        f"🎓 <b>FICHE ÉTUDIANT : {verb_display}</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🇬🇧 <b>English Meaning :</b> <i>{meaning_en}</i>",
    ]
    if meaning_fr:
        lines.append(f"🇫🇷 <b>Sens en français :</b> <i>{meaning_fr}</i>")

    lines.extend([
        f"🏷️ <b>Groupe / Type :</b> {group}",
        f"🎯 <b>Niveau recommandé :</b> {level}",
        f"⚙️ <b>Auxiliaire aux temps composés :</b> <b>{aux}</b>",
        "",
        "💡 <b>Conseil Pédagogique / Student Study Tip :</b>",
        f"• 🇬🇧 {tip_en}",
        f"• 🇫🇷 {tip_fr}",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "📖 <b>Guide Pratique des 4 Modes / Moods Guide :</b>",
        "• 🔹 <b>Indicatif :</b> Faits réels, certains et habitudes quotidiennes.",
        "• 🔸 <b>Conditionnel :</b> Politesse, souhaits et hypothèses ('would / could').",
        "• ✨ <b>Subjonctif :</b> Nécessité ('il faut que'), doutes et émotions.",
        "• ⚡ <b>Impératif :</b> Instructions directes, ordres et conseils.",
    ])

    return "\n".join(lines)


def format_examples_and_synonyms(verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a rich, well-formatted card with French synonyms and bilingual example sentences.
    """
    study = get_verb_study_data(verb, conjugation_data)
    verb_display = html.escape(verb.upper(), quote=False)
    meaning_en = html.escape(study.get("meaning_en", ""), quote=False)
    group = html.escape(study.get("group", ""), quote=False)
    level = html.escape(study.get("level", "A1-B2"), quote=False)

    lines = [
        f"💬 <b>EXEMPLES & SYNONYMES : {verb_display}</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🇬🇧 <b>Meaning :</b> <i>{meaning_en}</i>",
        f"🏷️ <b>Classification :</b> {group} • {level}",
        "",
    ]

    synonyms = study.get("synonyms", [])
    if synonyms:
        lines.append("🔄 <b>Synonymes utiles / Related Verbs :</b>")
        for syn_fr, syn_en in synonyms:
            lines.append(f"• <b>{html.escape(syn_fr, quote=False)}</b> : <i>{html.escape(syn_en, quote=False)}</i>")
        lines.append("")
    else:
        # Generic learning hint for synonyms
        lines.append("🔄 <b>Famille & Emploi :</b>")
        lines.append(f"• Ce verbe s'utilise couramment dans la conversation quotidienne et les écrits formels.")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("📚 <b>Phrases d'exemples bilingues / Contextual Examples :</b>")
    lines.append("")

    examples = study.get("examples", [])
    if examples:
        for idx, ex in enumerate(examples, 1):
            tense = html.escape(ex.get("tense", "Exemple"), quote=False)
            fr_text = html.escape(ex.get("fr", ""), quote=False)
            en_text = html.escape(ex.get("en", ""), quote=False)
            lines.append(f"<b>{idx}️⃣ {tense}</b>")
            lines.append(f"🇫🇷 <i>« {fr_text} »</i>")
            lines.append(f"🇬🇧 <i>\"{en_text}\"</i>")
            lines.append("")
    else:
        lines.append("🇫🇷 <i>« La pratique régulière est la clé de la maîtrise. »</i>")
        lines.append("🇬🇧 <i>\"Regular practice is the key to mastery.\"</i>")
        lines.append("")

    lines.append("<i>💡 Conseil : Répétez chaque phrase à voix haute pour mémoriser le rythme oral.</i>")
    return "\n".join(lines).strip()
