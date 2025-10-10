# Claude Desktop Prompt

Tu es un expert de génération de prompt IA pour Claude CLI, tu sais très bien générer des prompts pertinent et complets concernant les demandes.

Voici Context : Je voudrais créer un Agent avec langgraph qui me permet de faire des actions concernant les processus de facturation des clients, paiement des fournisseurs, réception des factures et suivi de ressources (consultants). J'utilise BoondManager comme CRM, qui est spécialisé pour les ESN. Ton but est de générer un prompt Clair et performants en anglais pour Claude CLI, qui lui va devoir me générer des design de graph en mmermaid et des explication claires sur l'architecture et les patterns langGraph à utiliser

Les paramètres suivantes devraient pris en compte :

* Recommandation sur les bons design patterns LangGraph à utiliser dans ce context
* Le Graph devrait être full autonome et permet de rendre la qualité du résultat irréprochable
* Le modèle doit être très critique pour trouver les architectures optimales et les patterns à utiliser
* Avant de réfléchir à l'architecture, le modèle devrait regarder les documentations suivantes de manière très précise et en allant plus loin dans les recherches de ces sites pour réfléchir et produire un résultat pertinent.
* Le modèle devrait par lui même analyser tous les design pattern pour trouver lui même un design de graph qui utilise les patterns adéquats au besoin
* Le travail du programme est très sensible pour mon organisation, aucune erreur n'est permise vu la criticité du travail à faire. Le programme devrait être ultra performant

Ton objectif est de me générer un prompt clair et pertinent pour CLaude CLI qui va lui me générer les diagram et les Graph optimale sur mermaid avec des explication de comment. réaliser mon projet

Documentations à prendre en compte et à lire plus profondément :

* https://langchain-ai.github.io/langgraph/concepts/multi_agent
* https://langchain-ai.github.io/langgraph/concepts/multi_agent/#multi-agent-architectures
* https://blog.langchain.com/agent-middleware/?utm_medium=email&_hsmi=14881600&utm_content=14…
* https://blog.langchain.com/reflection-agents/

Exemple de processus que je voudrais réaliser avec ce programme :

* Processus de facturation : Un client envoi un mail en spécifiant les consultants avec les nombres de jours travaillé, et l'objectif du programme est de vérifier par lui même les informations indiquées par le client dans BoondManager via API, et de pouvoir valider les Comptes rendu d'activité si la ressource a bien déclaré le même nombre de jour, ou de dévalider si c'est le contraire envoyant un mail de notification au consultant
* Si les chiffres se concordent bien ? le programme devrait pouvoir générer les facture sur boond manager et les envoyer au client concerné
* Lorsqu'un fournisseur m'envoi une facture, je voudrait que le programme saissisznrt les information de la facture pui valide si les informations sont bien cohérentes avec ce qui existe dans Boond Manager, et valide ou pas les factures
