"""
Compagnons recrutables — officiers nommés et hôtesses de taverne.

Deux mécaniques de recrutement :

  1. **Hôtesses de taverne** (une par port) : se recrutent à force de
     cadeaux. Compteur d'affection par port dans state.affection[port_id].
     Chaque visite à la taverne, après « Boire avec l'équipage », a une
     chance que l'hôtesse vienne s'asseoir à la table du capitaine :
     c'est la *rencontre*, déclenchée par data/actions.py
     (`_tavern_hostess_encounter`). À chaque rencontre, le joueur peut
     offrir UN cadeau unique. Au seuil d'affection, la rencontre
     suivante propose le recrutement et clôt la chaîne.

     Chaque hôtesse possède donc :
        - gift_cost / gift_flavor : le cadeau-type (un seul par stade)
        - gifts_needed             : seuil d'affection pour le recrutement
        - intro                    : ligne d'introduction (legacy)
        - encounter_dialogues      : liste de gifts_needed+1 répliques
                                     (une par stade, dernière = « prête à partir »)
        - accept                   : ligne au moment du recrutement

  2. **Officiers / spécialistes** : se recrutent via des événements
     (de port ou en mer) avec conditions historiques. Cf. port_events.py.

Chaque compagnon apporte un dict `bonuses`. Deux types de bonus existent :

  * **Bonus de statistique** (additifs avec ceux du capitaine) :
      combat, intimidation, navigation, leadership, discipline, stealth

  * **Modificateurs de mécanique** (additifs, capés où nécessaire) :
      morale_floor          : plancher de moral (max parmi tous)
      morale_per_turn       : régénération automatique par tour
      supply_savings        : fraction de vivres économisée (0-0.7)
      repair_discount       : ristourne sur réparation (0-0.6)
      recruit_discount      : ristourne sur embauche (0-0.5)
      fence_bonus           : bonus sur taux de recel (0-0.2)
      desertion_reduction   : réduction des désertions (0-0.8)
      crew_save_chance      : chance d'annuler la moitié d'une perte d'équipage
      scurvy_resist         : 1 = annule scorbut
      hull_per_turn         : régénération de coque par tour
      speed_bonus           : ajout direct au score de vitesse
      spanish_intel         : 1 = révèle les convois espagnols
      event_intel           : 1 = annonce le titre d'un événement avant choix

Pour AJOUTER un compagnon : compléter COMPANIONS plus bas.
Pour qu'il soit recrutable, il faut soit qu'il soit déclaré « hôtesse »
(port défini), soit qu'un événement appelle `state.add_companion(...)`.

Convention d'image : assets/images/companions/<id>.png
"""

COMPANIONS = {

    # ===============================================================
    # HÔTESSES DE TAVERNE — une par port, recrutement par cadeaux
    # ===============================================================

    "marie_tessart": {
        "id": "marie_tessart",
        "name": "Marie Tessart",
        "nickname": "L'Acadienne",
        "type": "tavern_keeper",
        "role": "Hôtesse de la Cayonne",
        "port": "tortuga",
        "period": "Antilles, vers 1670-1685",
        "biography": (
            "Acadienne déportée par les Anglais après 1654, recasée à "
            "Tortuga avec son père bateleur. Tient la salle basse de la "
            "Cayonne. Connaît tous les capitaines de passage."
        ),
        "bonuses": {
            "fence_bonus": 0.05,
            "morale_floor": 30,
        },
        "bonus_label": "Receleuse aguerrie (+5% au recel, moral plancher 30)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 30,
            "gifts_needed": 3,
            "gift_flavor": "un coupon de toile d'Hollande",
            "intro": (
                "Marie remplit votre godet sans vous regarder. « Encore "
                "un capitaine qui croit qu'on l'attend. »"
            ),
            # 4 répliques : aff 0, 1, 2, puis « prête à partir » au seuil.
            "encounter_dialogues": [
                (
                    "Marie pose un pichet d'étain devant vous sans vous "
                    "regarder. « On a parlé de toi à la résidence, "
                    "capitaine. Un dénommé d'Ogeron pose des questions. "
                    "C'est ton ami ? »"
                ),
                (
                    "Marie s'attable un instant en face de vous, le coupon "
                    "précédent toujours plié dans sa poche. « Mon père "
                    "était sablais. Mon mari, micmac. Et toi, capitaine, "
                    "d'où tu viens, exactement ? »"
                ),
                (
                    "Marie fait glisser un verre de tafia dans votre main. "
                    "« Trois fois que je te vois. Tu reviendras à la "
                    "prochaine escale, ou tu pars pour de bon ? J'ai "
                    "besoin de savoir, capitaine. »"
                ),
                (
                    "Marie pose son tablier sur la barrique sans un mot, "
                    "puis se penche : « Capitaine, mon balluchon est plié "
                    "depuis trois jours. Tu n'as qu'à dire un mot. »"
                ),
            ],
            "accept": (
                "Marie pose son tablier. « Trois mois que j'attendais "
                "qu'un imbécile me propose enfin. » Elle prend son "
                "balluchon et suit vers la chaloupe."
            ),
        },
    },

    "bess_watson": {
        "id": "bess_watson",
        "name": "Bess Watson",
        "nickname": "Bess la Rousse",
        "type": "tavern_keeper",
        "role": "Hôtesse du Cat and Fiddle",
        "port": "port_royal",
        "period": "Jamaïque, 1680-1692",
        "biography": (
            "Fille d'un transporté écossais après la révolte de Monmouth "
            "(1685). Sert au Cat and Fiddle. Sait quels marchands "
            "désarment et quels capitaines paient en bons écus."
        ),
        "bonuses": {
            "desertion_reduction": 0.5,
            "morale_per_turn": 1,
        },
        "bonus_label": "Tient les hommes à carreau (-50% désertion, +1 moral/tour)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 40,
            "gifts_needed": 3,
            "gift_flavor": "une livre de tabac de Virginie",
            "intro": (
                "Bess vous toise. « Sir Henry Morgan venait ici aussi. "
                "Vous n'êtes pas Morgan. »"
            ),
            "encounter_dialogues": [
                (
                    "Bess remplit votre godet jusqu'au bord, sans cesser de "
                    "vous fixer. « Sir Henry Morgan s'asseyait à cette "
                    "table. Vous n'êtes pas Morgan. Ça reste à voir si "
                    "c'est un défaut. »"
                ),
                (
                    "Bess s'accoude à la barrique, voix plus basse. "
                    "« Mon père a été transporté après Bothwell Bridge. "
                    "Mort à Spanish Town, sous le fouet d'un planteur "
                    "anglais. Et toi, capitaine — un jour, qui dira "
                    "d'où tu viens ? »"
                ),
                (
                    "Bess pose la nouvelle livre de tabac à côté de la "
                    "précédente, alignées sur l'étain. « Trois livres "
                    "en trois mois. Ou tu m'achètes ma compagnie, ou "
                    "tu m'achètes ma confiance. Choisis. »"
                ),
                (
                    "Bess décroche sa chevillière de l'enseigne du Cat "
                    "and Fiddle. « Cette ville sombrera un jour, "
                    "capitaine — un séisme, un pirate, un incendie, peu "
                    "importe. Je préfère sombrer avec un capitaine "
                    "vivant. »"
                ),
            ],
            "accept": (
                "Bess plie son tablier. « Cette ville sombre, autant que "
                "ce soit en mer. »"
            ),
        },
    },

    "hannah_mott": {
        "id": "hannah_mott",
        "name": "Hannah Mott",
        "nickname": "La Veuve",
        "type": "tavern_keeper",
        "role": "Hôtesse de Nassau",
        "port": "nassau",
        "period": "Bahamas, 1710-1718",
        "biography": (
            "Veuve d'un capitaine corsaire pendu à La Havane en 1712. "
            "Tient la maison sur la pointe. Connaît les Articles par "
            "cœur — elle les a copiés trois fois pour des capitaines."
        ),
        "bonuses": {
            "discipline": 1,
            "event_intel": 1,
        },
        "bonus_label": "Femme avisée (discipline +1, devine les événements)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 35,
            "gifts_needed": 3,
            "gift_flavor": "un livre de prières relié",
            "intro": (
                "Hannah essuie un gobelet d'étain. « J'en ai vu défiler, "
                "des capitaines. Trois mois et plus de nouvelles. »"
            ),
            "encounter_dialogues": [
                (
                    "Hannah essuie un gobelet d'étain avec lenteur, "
                    "ses doigts encore noircis d'encre des Articles "
                    "qu'elle copie le matin. « Mon mari est mort en mer "
                    "en 1712. À La Havane, au bout d'une corde. Vous, "
                    "capitaine, comment voulez-vous finir ? »"
                ),
                (
                    "Hannah relit silencieusement le livre de prières "
                    "que vous lui avez offert. « Les Articles disent "
                    "que chaque homme a sa part, et que le quartier-"
                    "maître veille au partage. Le savez-vous par cœur, "
                    "capitaine, ou faites-vous semblant ? »"
                ),
                (
                    "Hannah pose une copie des Articles entre vous deux, "
                    "encre fraîche. « Une troisième fois. Si je devais "
                    "signer quelque chose un jour, ce serait avec celui "
                    "qui me regarde en face quand il jure. »"
                ),
                (
                    "Hannah enroule les Articles dans un mouchoir et les "
                    "glisse dans son tablier. « Si vous me demandez de "
                    "monter à bord, capitaine, je dirai oui. Je n'ai "
                    "plus rien à enterrer dans cette ville. »"
                ),
            ],
            "accept": (
                "Hannah enroule les Articles dans un mouchoir. « Si je "
                "dois mourir en mer, autant que ce soit avec un nouveau. »"
            ),
        },
    },

    "mahalia": {
        "id": "mahalia",
        "name": "Mahalia",
        "nickname": "La Sakalava",
        "type": "tavern_keeper",
        "role": "Hôtesse du comptoir de Baldridge",
        "port": "ile_sainte_marie",
        "period": "Madagascar, 1693-1700",
        "biography": (
            "Née sur la côte sakalava de Madagascar, mariée puis libérée "
            "d'un négociant hollandais. Parle malgache, français et "
            "anglais portuaire. Connaît les plantes anti-fièvre."
        ),
        "bonuses": {
            "supply_savings": 0.20,
            "scurvy_resist": 1,
        },
        "bonus_label": "Connaît les herbes (vivres -20%, immunise du scorbut)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 40,
            "gifts_needed": 3,
            "gift_flavor": "un collier de perles de Bahreïn",
            "intro": (
                "Mahalia broie une racine dans un mortier. « Vous puez "
                "la mer, capitaine. Et le rhum. »"
            ),
            "encounter_dialogues": [
                (
                    "Mahalia broie une racine dans son mortier sans lever "
                    "les yeux. « Vous puez encore la mer, capitaine. Et "
                    "vos hommes toussent — je les entends d'ici. Le "
                    "scorbut, ça se sent à la sueur. »"
                ),
                (
                    "Mahalia trie ses sachets d'écorces de quinquina. "
                    "« Le précédent collier, je l'ai gardé. Pas par "
                    "sentiment — par curiosité. Tu paies bien, "
                    "capitaine, mais pourquoi moi, et pas une autre ? »"
                ),
                (
                    "Mahalia vous regarde longuement, perles à la main. "
                    "« Trois fois. Tes hommes tomberont moins si je "
                    "viens à bord, c'est vrai. Mais toi, capitaine — "
                    "qu'est-ce que tu as à offrir en dehors de tes "
                    "pièces ? »"
                ),
                (
                    "Mahalia met de côté ses sachets d'écorces dans un "
                    "petit coffre de bois rouge. « Mes herbes voyageront "
                    "mieux à ton bord qu'à terre. Et le roi sakalava "
                    "n'a plus besoin de moi. »"
                ),
            ],
            "accept": (
                "Mahalia rassemble ses sachets d'écorces. « Tes hommes "
                "tomberont moins si je viens. »"
            ),
        },
    },

    "beatriz_castano": {
        "id": "beatriz_castano",
        "name": "Beatriz Castaño",
        "nickname": "La Andaluza",
        "type": "tavern_keeper",
        "role": "Hôtesse exilée à La Havane",
        "port": "la_havane",
        "period": "Cuba, 1690-1710",
        "biography": (
            "Andalouse, ancienne danseuse expulsée pour scandale. Sert "
            "dans un bouge des bas-quartiers de La Havane. Hostile aux "
            "officiers du Roi catholique, qui l'ont chassée."
        ),
        "bonuses": {
            "spanish_intel": 1,
            "combat": 1,
        },
        "bonus_label": "Sait où passent les galions (combat +1)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 50,
            "gifts_needed": 2,    # plus difficile d'accès, mais moins de visites
            "gift_flavor": "une émeraude des mines de Muzo",
            "intro": (
                "Beatriz vous fixe entre deux notes de guitare. « Tu n'es "
                "pas espagnol. Bien. »"
            ),
            # 3 répliques (gifts_needed=2 +1) : aff 0, 1, puis seuil.
            "encounter_dialogues": [
                (
                    "Beatriz pose sa guitare et vous toise entre deux "
                    "accords. « Tu n'es pas espagnol. Bien. J'ai eu mon "
                    "compte d'officiers du Roi Catholique — et eux du "
                    "mien, depuis Séville. »"
                ),
                (
                    "Beatriz cache la première émeraude dans sa basquine, "
                    "sous la jupe. « Je connais les routes des galions, "
                    "capitaine. Et leurs vices. Tu veux savoir lesquels, "
                    "ou tu veux juste m'acheter avec une autre pierre ? »"
                ),
                (
                    "Beatriz attache un couteau court sous sa basquine, "
                    "geste rapide, qu'elle ne cherche pas à cacher. "
                    "« Tu me sors d'ici, je te sors des galions. Vamos, "
                    "capitán. »"
                ),
            ],
            "accept": (
                "Beatriz cache un couteau dans sa basquine. « Vamos. "
                "Je connais leurs routes mieux qu'eux. »"
            ),
        },
    },

    "sarah_pemberton": {
        "id": "sarah_pemberton",
        "name": "Sarah Pemberton",
        "nickname": None,
        "type": "tavern_keeper",
        "role": "Hôtesse à Charles Town",
        "port": "charleston",
        "period": "Caroline, 1700-1718",
        "biography": (
            "Fille d'un planteur quaker ruiné par une mauvaise récolte "
            "d'indigo. Sait écrire, lire, tenir un livre de comptes. "
            "Sert au Pink House, taverne respectable du port."
        ),
        "bonuses": {
            "recruit_discount": 0.25,
            "morale_per_turn": 1,
        },
        "bonus_label": "Sait engager les hommes (-25% sur le recrutement)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 45,
            "gifts_needed": 3,
            "gift_flavor": "une rame de papier de Hollande et une plume",
            "intro": (
                "Sarah tient sa plume comme une dague. « Vous savez "
                "écrire, capitaine ? Pas tous. »"
            ),
            "encounter_dialogues": [
                (
                    "Sarah note quelque chose dans son livre de comptes "
                    "puis lève la plume vers vous. « Vous savez écrire, "
                    "capitaine ? Pas tous. Et ceux qui me proposent "
                    "quelque chose, encore moins. »"
                ),
                (
                    "Sarah relit ses propres notes à voix basse, comme "
                    "pour elle-même. « Le papier que vous m'avez donné, "
                    "je l'ai gardé pour mes livres de bord. Vous "
                    "parliez sérieusement, capitaine, ou c'était un "
                    "geste d'oisif ? »"
                ),
                (
                    "Sarah ferme son grand livre d'un geste net. « Trois "
                    "ramettes. Trois venues. Mon père, qui était de "
                    "l'Assemblée des Amis, disait : compter, c'est "
                    "s'engager. À vous de me dire ce que vous comptez "
                    "de moi. »"
                ),
                (
                    "Sarah replie son livre de comptes et le glisse "
                    "dans une besace de toile. « J'ai fini d'écrire "
                    "pour Charles Town. Le prochain registre, capitaine, "
                    "ce sera le vôtre. »"
                ),
            ],
            "accept": (
                "Sarah ferme son livre de comptes. « Si je dois sortir "
                "de cette ville, autant que ce soit en mer. »"
            ),
        },
    },

    "marguerite_lavigne": {
        "id": "marguerite_lavigne",
        "name": "Marguerite Lavigne",
        "nickname": "Margot la Manchotte",
        "type": "tavern_keeper",
        "role": "Hôtesse de Petit-Goâve",
        "port": "saint_domingue",
        "period": "Saint-Domingue, 1685-1700",
        "biography": (
            "Veuve d'un engagé picard, a perdu un bras dans la tempête "
            "de 1681 qui a balayé Léogâne. Tient le bouge des flibustiers. "
            "A appris à recoudre les plaies plus vite que personne."
        ),
        "bonuses": {
            "crew_save_chance": 0.30,
            "morale_per_turn": 1,
        },
        "bonus_label": "Sait recoudre (30% de chances de sauver des pertes)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 35,
            "gifts_needed": 3,
            "gift_flavor": "une trousse d'instruments en argent",
            "intro": (
                "Margot saisit son verre du bras qui lui reste. "
                "« On dit que tu paies bien, capitaine. On dit. »"
            ),
            "encounter_dialogues": [
                (
                    "Margot soulève son verre du bras valide, l'autre "
                    "manche pendante et nouée. « Mon mari est mort "
                    "dans la tempête de 81, à Léogâne. Depuis, je "
                    "recouds. Et toi, capitaine — tu paies les "
                    "chirurgiens, ou tu les laisses crever sur la "
                    "plage avec les blessés ? »"
                ),
                (
                    "Margot range la première trousse d'instruments "
                    "dans un coffre, sous le comptoir. « Tu paies en "
                    "argent, pas en promesse. C'est rare. Tu cherches "
                    "quelqu'un pour recoudre, capitaine, ou pour autre "
                    "chose que je préfère ne pas nommer ? »"
                ),
                (
                    "Margot ferme la besace d'instruments à la sangle "
                    "de cuir, d'une main experte. « Trois fois. J'ai "
                    "fini de te jauger, capitaine. Si je sors d'ici, "
                    "ce sera pour la mer ou pour la tombe, et je "
                    "préfère la mer. »"
                ),
                (
                    "Margot endosse la besace d'instruments en bandoulière, "
                    "sa main valide ajustant la sangle. « Tu as un "
                    "charpentier ? Tu auras une recouseuse aussi. Et "
                    "Petit-Goâve peut crever sans moi. »"
                ),
            ],
            "accept": (
                "Margot accroche une besace d'instruments. « Quelqu'un "
                "doit recoudre vos hommes. Ce sera moi. »"
            ),
        },
    },

    # ===============================================================
    # OFFICIERS / SPÉCIALISTES — recrutés via événements
    # ===============================================================

    "israel_hands": {
        "id": "israel_hands",
        "name": "Israel Hands",
        "nickname": None,
        "type": "officer",
        "role": "Maître canonnier",
        "port": None,
        "period": "Caraïbes, 1716-1718 (historique)",
        "biography": (
            "Servit comme second sur le Queen Anne's Revenge sous Edward "
            "Teach. Réputé pour son tir au canon. Survécut au combat "
            "d'Ocracoke en 1718, finit ses jours mendiant à Londres."
        ),
        "bonuses": {
            "combat": 2,
        },
        "bonus_label": "Tire au mille (combat +2)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un grand maigre au front balafré vous aborde sur le quai. "
                "« Israel Hands. J'ai servi sous Teach. Je tire au canon "
                "comme un autre signe son nom. »"
            ),
        },
    },

    "walter_kennedy": {
        "id": "walter_kennedy",
        "name": "Walter Kennedy",
        "nickname": None,
        "type": "officer",
        "role": "Quartier-maître",
        "port": None,
        "period": "Atlantique, 1719-1721 (historique)",
        "biography": (
            "Voleur des bas quartiers de Londres devenu pirate sur le "
            "Royal Rover de Howell Davis puis Bartholomew Roberts. Sait "
            "lire les hommes et tenir les Articles. Mauvaise fin : trahi "
            "et pendu à Wapping."
        ),
        "bonuses": {
            "leadership": 2,
            "desertion_reduction": 0.5,
        },
        "bonus_label": "Quartier-maître redouté (leadership +2, -50% désertion)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un Londonien au regard fuyant vous trouve à la taverne. "
                "« Walter Kennedy. Je sais conduire les hommes. Je sais "
                "aussi quand un capitaine devient un poids. »"
            ),
        },
    },

    "john_cole_surgeon": {
        "id": "john_cole_surgeon",
        "name": "John Cole",
        "nickname": "Le Chirurgien",
        "type": "officer",
        "role": "Chirurgien de bord",
        "port": None,
        "period": "Atlantique, 1700-1730",
        "biography": (
            "Médecin de Boston expulsé pour faux diplôme. N'a jamais "
            "tué un homme avec sa scie, ce qui est rare au XVIIIe siècle. "
            "Sur les navires pirates, on prenait souvent les chirurgiens "
            "de force, mais Cole, lui, signe les Articles."
        ),
        "bonuses": {
            "crew_save_chance": 0.40,
            "scurvy_resist": 1,
        },
        "bonus_label": "Chirurgien compétent (40% de saves, immunise du scorbut)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un homme en redingote tachée descend à pas pressés. "
                "« John Cole. La justice de Boston me veut. Embarquez-moi, "
                "je vous sers de chirurgien. »"
            ),
        },
    },

    "yusuf_le_maure": {
        "id": "yusuf_le_maure",
        "name": "Yusuf",
        "nickname": "Le Maure",
        "type": "officer",
        "role": "Maître pilote",
        "port": None,
        "period": "Atlantique, 1690-1720",
        "biography": (
            "Né dans une famille de pilotes barbaresques, capturé enfant "
            "lors d'une attaque maltaise, libéré à Marseille. A appris "
            "les cartes hollandaises, anglaises, françaises et arabes. "
            "Connaît les courants de l'Atlantique comme nul autre."
        ),
        "bonuses": {
            "navigation": 2,
            "speed_bonus": 1,
        },
        "bonus_label": "Maître pilote (navigation +2, vitesse +1)",
        "recruitment": {
            "method": "event",
            "intro": (
                "L'homme parle un français impeccable et trace des "
                "lignes sur le sable du doigt. « Yusuf. Je connais "
                "l'Atlantique mieux que mon nom. »"
            ),
        },
    },

    "pere_etienne": {
        "id": "pere_etienne",
        "name": "Étienne de Mortain",
        "nickname": "Le père Étienne",
        "type": "officer",
        "role": "Aumônier déchu",
        "port": None,
        "period": "1690-1720",
        "biography": (
            "Bénédictin de Cluny, écarté de l'ordre pour usure et "
            "fréquentations équivoques à Nantes. Lit le latin, tient "
            "les comptes, dit l'office quand on le lui demande."
        ),
        "bonuses": {
            "morale_per_turn": 2,
            "morale_floor": 30,
        },
        "bonus_label": "Discours bien sentis (+2 moral/tour, plancher 30)",
        "recruitment": {
            "method": "event",
            "intro": (
                "L'homme en bure tachée, seul survivant d'une épave, "
                "lève une main sale. « Étienne de Mortain, bénédictin "
                "déchu. Dieu et moi nous fâchons souvent. »"
            ),
        },
    },

    "jean_boudin": {
        "id": "jean_boudin",
        "name": "Jean Boudin",
        "nickname": "Le Cuistot",
        "type": "officer",
        "role": "Cuisinier de bord",
        "port": None,
        "period": "Saint-Domingue, 1685-1715",
        "biography": (
            "Ancien marmiton à la résidence du gouverneur de Saint-Domingue. "
            "Sait tirer trois soupes d'un baril de bœuf salé. Renvoyé "
            "pour avoir bu le bordeaux de Monsieur du Casse."
        ),
        "bonuses": {
            "supply_savings": 0.30,
            "morale_per_turn": 1,
        },
        "bonus_label": "Économise le baril (vivres -30%, +1 moral/tour)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un gros homme à tablier de cuir fait signe. « Jean "
                "Boudin. Je nourris cinquante hommes avec ce que d'autres "
                "donnent à trente. »"
            ),
        },
    },

    "mary_lacy_carpenter": {
        "id": "mary_lacy_carpenter",
        "name": "Mary Lacy",
        "nickname": "Le maître charpentier en culottes",
        "type": "officer",
        "role": "Maître charpentier",
        "port": None,
        "period": "Atlantique, 1700-1730",
        "biography": (
            "Embarquée à quinze ans déguisée en garçon sous le nom de "
            "William Chandler. Devenue maître charpentier à force. Inspirée "
            "des cas historiques de Hannah Snell et Mary Lacy."
        ),
        "bonuses": {
            "repair_discount": 0.30,
            "hull_per_turn": 1,
        },
        "bonus_label": "Charpentier hors pair (-30% réparation, +1 coque/tour)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un jeune charpentier au timbre étrangement aigu vous "
                "tend une plane. « Embauchez-moi à la place de votre "
                "ancien — j'ai vu ce qu'il a fait à votre bordage. »"
            ),
        },
    },

    "vieux_tom_buccaneer": {
        "id": "vieux_tom_buccaneer",
        "name": "Vieux Tom",
        "nickname": "Le Boucanier",
        "type": "officer",
        "role": "Boucanier tireur d'élite",
        "port": None,
        "period": "Hispaniola, 1670-1700",
        "biography": (
            "Trente ans à fumer le bœuf sauvage dans les collines de "
            "Saint-Domingue. Tire au long fusil à 200 pas. A connu "
            "l'Olonnais et n'aime pas en parler."
        ),
        "bonuses": {
            "combat": 1,
            "intimidation": 1,
        },
        "bonus_label": "Tireur des bois (combat +1, intimidation +1)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un vieil homme sec, fusil de boucanier sur l'épaule, "
                "vous dévisage. « Tom. J'ai fumé la viande trop "
                "longtemps. Je veux voir la mer avant de mourir. »"
            ),
        },
    },
}


# ---------------------------------------------------------------
# Helpers d'accès
# ---------------------------------------------------------------

def get_companion(companion_id: str) -> dict:
    return dict(COMPANIONS[companion_id])


def get_tavern_keeper(port_id: str):
    """Renvoie l'hôtesse associée à un port, ou None."""
    for c in COMPANIONS.values():
        if c.get("type") == "tavern_keeper" and c.get("port") == port_id:
            return dict(c)
    return None


def list_companions() -> list:
    return list(COMPANIONS.values())


# ---------------------------------------------------------------
# Application des bonus
# ---------------------------------------------------------------

# Bonus de statistique (additifs, pas de cap)
STAT_BONUSES = {"combat", "intimidation", "navigation",
                "leadership", "discipline", "stealth"}

# Modificateurs « pourcentage » avec un plafond pour éviter les abus
CAPPED_MODIFIERS = {
    "supply_savings":      0.70,
    "repair_discount":     0.60,
    "recruit_discount":    0.50,
    "fence_bonus":         0.20,
    "desertion_reduction": 0.80,
    "crew_save_chance":    0.70,
}

# Modificateurs additifs sans plafond
ADDITIVE_MODIFIERS = {"morale_per_turn", "hull_per_turn", "speed_bonus"}

# Modificateurs « max » (on prend la valeur la plus forte)
MAX_MODIFIERS = {"morale_floor"}

# Modificateurs binaires
BINARY_MODIFIERS = {"scurvy_resist", "spanish_intel", "event_intel"}


def aggregate_bonuses(captain_bonuses: dict, companions: list) -> dict:
    """
    Combine les bonus du capitaine + ceux des compagnons, en appliquant
    les règles de chaque catégorie (somme, somme avec cap, max, ou OU logique).
    """
    out = {}

    def _collect(name):
        vals = []
        if name in captain_bonuses:
            vals.append(captain_bonuses[name])
        for c in companions:
            if name in c.get("bonuses", {}):
                vals.append(c["bonuses"][name])
        return vals

    for name in STAT_BONUSES | ADDITIVE_MODIFIERS:
        vals = _collect(name)
        if vals:
            out[name] = sum(vals)

    for name, cap in CAPPED_MODIFIERS.items():
        vals = _collect(name)
        if vals:
            out[name] = min(cap, sum(vals))

    for name in MAX_MODIFIERS:
        vals = _collect(name)
        if vals:
            out[name] = max(vals)

    for name in BINARY_MODIFIERS:
        vals = _collect(name)
        if vals:
            out[name] = 1 if any(v for v in vals) else 0

    return out
