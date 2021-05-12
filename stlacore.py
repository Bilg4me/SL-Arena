import sqlite3
from random import random, randrange, choice

connexion = sqlite3.connect("stla.sqlite")
curseur = connexion.cursor()

MAX_JAUGE = 1000

# Constantes liées à la base de données
EF_DEGATS = 0
EF_SOIN = 1
EF_ENDORMI = 2
EF_SONNE = 3
EF_DEFENSE_PLUS = 4
EF_DEFENSE_MOINS = 5
EF_DEGATS_DOT = 6
EF_SOINS_DOT = 7
EF_VITESSE_PLUS = 8
EF_VITESSE_MOINS = 9
EF_JAUGE_MOINS = 10
EF_JAUGE_PLUS = 11
EF_PROVOCATION = 12
EF_ESQUIVE_GARANTIE = 13
EF_TACTIQUE = 14
EF_ASSISTANCE = 15

# Constantes de ciblage
CI_TOUS = 0
CI_ALEATOIRE = 1
CI_UNIQUE = 2
CI_VOISINNAGE = 3
CI_RANGEE = 4
CI_LANCEUR = 5
CI_AUTRES = 6

CI_JOUEUR = 0
CI_ADVERSAIRE = 1

EQ_JOUEUR = 0
EQ_ADVERSAIRE = 1

VICTOIRE_J1 = 0
VICTOIRE_J2 = 1
EGALITE = 2
PRET_AU_COMBAT = 3

PROBA_CRITIQUE = 0.2
# Symboles et phrases d'effets
symboles = ["", "", "Zz", "**", "D+", "D-", "DoT", "HoT", "V+", "V-", "", "", "!!","><", "@",""]
phrasesEffets = ["inflige des dégâts à", "soigne", "endort", "sonne", "augmente la défense de", "diminue la défense de", "inflige des dégâts sur plusieurs tours à", "soigne sur plusieurs tours", "augmente la vitesse de", "diminue la vitesse de", "vide une partie de la jauge de", "remplit une partie de la jauge de", "octroie provocation à", "garantit une esquive à", "octroie tactique à", "requiert l'assistance de"]

# Phrases de ciblage
phrasesCibles = ["tous", "une cible aléatoire", "la cible", "la cible et ses voisins", "la cible et sa rangée", "son lanceur", "ses coéquipiers"]

# Couleurs
blue = (0, 0, 255)
cyan = (0, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
lightgreen =(0, 128 ,0)

grey = (128, 128, 128)
black = (0, 0, 0)
white = (255, 255, 255)
yellow = (255, 255, 0)
historique = []
marron = (90, 58, 34)

orange = (255, 128, 255)

class Capacite:
    def __init__(self, caracteristiques):
        self.cid = caracteristiques[0]
        self.description = caracteristiques[1]
        self.recharge = caracteristiques[2]
        self.attente = 0
        
        self.occurences = [Occurence(o) for o in curseur.execute("SELECT eid, cible, ciblage, probabilite, intensite, duree FROM occurences WHERE cid = " + str(self.cid)).fetchall()]

class Occurence:
    def __init__(self, caracteristiques):
        self.eid = caracteristiques[0]
        self.cible = caracteristiques[1]
        self.ciblage = caracteristiques[2]
        self.probabilite = caracteristiques[3]
        self.intensite = caracteristiques[4]
        self.duree = caracteristiques[5]
        
class Personnage:
    def __init__(self, caracteristiques, equipe, emplacement):
        self.pid = caracteristiques[0]
        self.nom = caracteristiques[1]
        
        self.viebase = self.vie = caracteristiques[2]
        self.defensebase = self.defense = caracteristiques[4]
        self.forcebase = self.force = 100
        self.vitessebase = self.vitesse = caracteristiques[5]
        self.esquive = caracteristiques[3]
        
        self.effets = []
        self.capacites = [None]*3
        
        for i in range(3):
            caracteristiquesCapacite = curseur.execute("SELECT cid, description, recharge FROM capacites WHERE pid = " + str(self.pid)+ " AND emplacement = " + str(i)).fetchone()
            self.capacites[i] = Capacite(caracteristiquesCapacite)
            
        self.jauge = 0
        self.equipe = equipe
        self.emplacement = emplacement
        
    def subit_effet(self, effet):
        return effet in [eid for eid, _, _ in self.effets]
    
    def retire_effet(self, effet):
        for i in range(len(self.effets)):
            if self.effets[i][0] == effet:
                self.effets.pop(i)
                return
            
    def recalcule_stats(self):
        self.defense = self.defensebase
        self.force = self.forcebase
        self.vitesse = self.vitessebase
        
        for (eid, intensite, duree) in self.effets:
            if eid == EF_DEFENSE_PLUS:
                self.defense *= 2
            elif eid == EF_DEFENSE_MOINS:
                self.defense //= 2
            elif eid == EF_VITESSE_PLUS:
                self.vitesse *= 2
            elif eid == EF_VITESSE_MOINS:
                self.vitesse //= 2
                
class EtatJeu:
    def __init__(self):
        self.equipes = [[None]*10 for i in range(2)]
        self.cibles = [[(2,1), (2,1)] for i in range(2)] 
        self.historique = []
        self.doitJouer = None
        
    def memoriser(self, *args, couleur=white):
        self.historique.append((" ".join(str(arg) for arg in args),couleur))
        
    def change_cible_alliee(self, case, joueur):
        self.cibles[joueur][0] = case
    
    def change_cible_adverse(self, case, joueur):
        self.cibles[joueur][1] = case
        
    def donne_cible_alliee(self, joueur):
        if self.equipes[joueur][emplacement(self.cibles[joueur][0])] == None:
            for i in range(10):
                if self.equipes[joueur][i]!=None:
                    self.cibles[joueur][0] = coords(i)
                    break
            
        return self.cibles[joueur][0]
    
    def donne_cible_adverse(self, joueur):
        adversaire = 1 - joueur
        emplacementCible = emplacement(self.cibles[joueur][1])
        
        if self.equipes[adversaire][emplacementCible] == None:
            for i in range(10):
                if self.equipes[adversaire][i]!=None:
                    emplacementCible = i
                    break
        provocateurs = self.donne_provocateurs(adversaire)
        if provocateurs!=[] and emplacementCible not in provocateurs:
            emplacementCible = provocateurs[0]
        
        self.cibles[joueur][1] = coords(emplacementCible)
        
        return self.cibles[joueur][1]
    
    def donne_provocateurs(self, eq):
        emplacementProvocateurs = []
        for personnage in self.equipes[eq]:
            if personnage==None: continue
            if personnage.subit_effet(EF_PROVOCATION):
                emplacementProvocateurs.append(personnage.emplacement)
        return emplacementProvocateurs
    
    # renvoie VICTOIRE_J1, VICTOIRE_J2, EGALITE ou PRET_AU_COMBAT
    def debut_de_tour(self):
        # suppression des personnages morts
        for eq in EQ_JOUEUR, EQ_ADVERSAIRE:
            for personnage in self.equipes[eq]:
                if personnage!=None and personnage.vie == 0:
                    self.memoriser(personnage.nom, ["(joueur1)","(joueur2)"][personnage.equipe], "est épuisé et sort du combat", couleur=[green, red][personnage.equipe])
                    self.equipes[eq][personnage.emplacement] = None
            
        # vérification des conditions de fin de partie
        fin = 0
        if all(p==None for p in self.equipes[EQ_JOUEUR]):
            fin |= 1<<EQ_ADVERSAIRE
        
        if all(p==None for p in self.equipes[EQ_ADVERSAIRE]):
            fin |= 1<<EQ_JOUEUR
        if fin == 3:
            return EGALITE
        elif fin == 1:
            return VICTOIRE_J1
        elif fin == 2:
            return VICTOIRE_J2
        
        # détermination du personnage à jouer
        listePersonnages = [p for p in self.equipes[EQ_JOUEUR] + self.equipes[EQ_ADVERSAIRE] if p!=None]
        self.doitJouer = min(listePersonnages, key=lambda p:(MAX_JAUGE-p.jauge)/p.vitesse + random()/100)

        # mise à jour des jauges des personnages
        tempsAEcouler = (MAX_JAUGE-self.doitJouer.jauge)/self.doitJouer.vitesse
        for p in listePersonnages:
            p.jauge+=tempsAEcouler*p.vitesse
        
        # application des effets de début de tour
        vaJouer = True
        for i in range(len(self.doitJouer.effets)-1, -1, -1):                    
            (eid, intensite, duree) = self.doitJouer.effets[i]
            if eid in [EF_SONNE, EF_ENDORMI]:
                vaJouer = False
            if eid not in [EF_DEGATS_DOT, EF_SOINS_DOT]:
                continue
            
            if duree > 0:
                duree -= 1
            
            if eid == EF_DEGATS_DOT:
                self.doitJouer.vie -= (1+ (random()<0.2))*intensite
                self.doitJouer.vie = max(self.doitJouer.vie, 0)
            else:
                self.doitJouer.vie += (1+ (random()<0.2))*intensite
                self.doitJouer.vie = min(self.doitJouer.vie, self.doitJouer.viebase)
            
            if duree == 0:
                self.doitJouer.effets.pop(i)
            else:
                self.doitJouer.effets[i]=(eid, intensite, duree)
        
        if self.doitJouer.vie == 0:
            self.doitJouer = None
            return self.debut_de_tour()
        elif vaJouer==False:
            self.doitJouer.jauge = 0
            self.memoriser(self.doitJouer.nom, ["(joueur1)","(joueur2)"][self.doitJouer.equipe], "ne peut pas jouer", couleur=[green, red][self.doitJouer.equipe])
            self.fin_de_tour()
            return self.debut_de_tour()
        return PRET_AU_COMBAT
    
    def fin_de_tour(self):
        if self.doitJouer != None:
            # suppression des effets expirés et remise à 0 de la jauge
            self.doitJouer.jauge = 0
            for i in range(len(self.doitJouer.effets)-1, -1, -1):                
                (eid, intensite, duree) = self.doitJouer.effets[i]
                if eid in [EF_DEGATS_DOT, EF_SOINS_DOT, EF_ESQUIVE_GARANTIE]:
                    continue
                
                if duree > 0:
                    duree -= 1
                
                if duree == 0:
                    self.doitJouer.effets.pop(i)
                else:
                    self.doitJouer.effets[i]=(eid, intensite, duree)
            self.doitJouer.recalcule_stats()
            
    def applique_effet(self, occurence, lanceur):
        cibles = []
        caseCible = [self.donne_cible_alliee, self.donne_cible_adverse][occurence.cible](lanceur.equipe)
        equipeCible = self.equipes[occurence.cible!=lanceur.equipe]
        
        if occurence.ciblage==CI_UNIQUE:
            cibles.append(caseCible)
        elif occurence.ciblage==CI_ALEATOIRE:
            candidats = []
            for i in range(10):
                if equipeCible[i] != None:
                    candidats.append(i)
            cibles.append(coords(choice(candidats)))
        elif occurence.ciblage==CI_RANGEE:
            l,c = caseCible
            for i in range(5):
                cibles.append((i,c))
        elif occurence.ciblage==CI_VOISINNAGE:
            l,c = caseCible
            for i in range(5):
                for j in range(2):
                    if max(abs(i-l),abs(j-c))<=1:
                        cibles.append((i,j))
        elif occurence.ciblage==CI_TOUS:
            for i in range(5):
                for j in range(2):
                    cibles.append((i,j))
        elif occurence.ciblage==CI_LANCEUR:
            cibles.append(coords(lanceur.emplacement))
        elif occurence.ciblage==CI_AUTRES:
            for i in range(5):
                for j in range(2):
                    if emplacement((i,j))!=lanceur.emplacement:
                        cibles.append((i,j))
                        
        duree = occurence.duree
        
        for caseCible in cibles:
            empl = emplacement(caseCible)
            personnage = equipeCible[empl]
            if personnage != None:
                if occurence.eid == EF_DEGATS:
                    esquive = random() < personnage.esquive/100
                    if esquive or personnage.subit_effet(EF_ESQUIVE_GARANTIE):
                        if not esquive:
                            personnage.retire_effet(EF_ESQUIVE_GARANTIE)
                        phrase = ["->",personnage.nom, ["(joueur1)", "(joueur2)"][personnage.equipe], "esquive"]
                    else:
                        personnage.retire_effet(EF_ENDORMI)
                        intensite = occurence.intensite
                        if random() < PROBA_CRITIQUE:
                            phrase = ["->", personnage.nom, ["(joueur1)", "(joueur2)"][personnage.equipe], "subit un critique"]
                            intensite*=2
                        else:
                            phrase = ["->", personnage.nom, ["(joueur1)", "(joueur2)"][personnage.equipe], "subit l'attaque"]
                        coup = max(1, intensite-personnage.defense)
                        phrase.append("(-" + str(coup) +"pv)")
                        personnage.vie -= max(1, coup)
                        personnage.vie = max(0, personnage.vie)
                    self.memoriser(*phrase)
                elif occurence.eid == EF_ASSISTANCE:
                    self.applique_capacite(personnage.capacites[0], personnage)
                elif occurence.eid in (EF_JAUGE_MOINS, EF_JAUGE_PLUS):
                    personnage.jauge += (1 if (occurence.eid == EF_JAUGE_PLUS) else -1)*occurence.intensite*MAX_JAUGE//100
                    personnage.jauge = min(max(0,personnage.jauge), MAX_JAUGE)
                elif occurence.eid == EF_SOIN:
                    intensite = occurence.intensite
                    if random() < PROBA_CRITIQUE:
                        self.memoriser("->",personnage.nom, ["(joueur1)", "(joueur2)"][personnage.equipe], "reçoit un soin critique")
                        intensite *= 2
                    else:
                        self.memoriser("->",personnage.nom, ["(joueur1)", "(joueur2)"][personnage.equipe], "reçoit un soin")
                    personnage.vie += intensite
                    personnage.vie = min(personnage.vie, personnage.viebase)
                elif occurence.eid==EF_ESQUIVE_GARANTIE or occurence.eid not in [eid for (eid, _, _) in personnage.effets]:
                    if personnage == lanceur:
                        duree+=1
                    personnage.effets.append((occurence.eid, occurence.intensite, duree))
                    personnage.recalcule_stats()
                else:
                    for i in range(len(personnage.effets)):
                        if personnage.effets[i][0]==occurence.eid:
                            personnage.effets[i]=max(personnage.effets[i], (occurence.eid, occurence.intensite, duree))
                    

    def applique_capacite(self, capacite, lanceur):
        self.memoriser(lanceur.nom, ["(joueur1)", "(joueur2)"][lanceur.equipe],"utilise la capacité", capacite.description, couleur = [green, red][lanceur.equipe])
        for occurence in capacite.occurences:
            if random() < float(occurence.probabilite) or lanceur.subit_effet(EF_TACTIQUE):
                self.applique_effet(occurence, lanceur)
        
        for c in lanceur.capacites:
            c.attente = max(c.attente - 1, 0)
        
        capacite.attente = capacite.recharge
        
def emplacement(case):
    return case[0]+case[1]*5

def coords(emplacement):
    return (emplacement%5, emplacement//5)

def charge_personnage(pid, equipe, emplacement):
    resultatSQL = curseur.execute("SELECT pid, nom, vie, esquive, defense, vitesse FROM personnages WHERE pid = "+str(pid)).fetchone()
    return Personnage(resultatSQL, equipe, emplacement)

def initialise_equipe(equipeNumeros, equipe):
    equipePersonnages = [None for i in range(10)]
    for i in range(10):
        if equipeNumeros[i]!=None:
            equipePersonnages[i] = charge_personnage(equipeNumeros[i], equipe, i)
    return equipePersonnages
