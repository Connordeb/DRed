import itertools
import glog
import csv
from parser import Parser
import os
from rule import Rule
import copy
from literal import Literal
import numpy as np
import random

loglevel = 5 # INFO level
glog.set_logging_level(loglevel)

"""Uncomment below for dbpedia """
# main_dir = "/home/connor/PycharmProjects/final/glog-python-master/src/dbpedia/dbpedia"
# rule_location = "DBpedia_L.linear.dlog"

""" Uncomment below for small example"""
main_dir = "/home/connor/PycharmProjects/final/glog-python-master/src/python/example1_update" # Location of example.dlog and edb.conf
rule_location = "example1.dlog"

os.chdir(main_dir)
edb_file = 'edb.conf'
chaseProcedure = "tgchase"
typeProv = "NODEPROV"
seed = 0
np.random.seed(seed)
random.seed(seed)
deletion_suffix = "_del"
copy_suffix = "_new"
insertion_suffix = "_ins"
placeholder = "z"
parser = Parser()


def print_all_rules(program):
    n_rules = program.get_n_rules()
    for i in range(n_rules):
        print(i, " ", program.get_rule(i))


class DRed_updater:    
    def __init__(self, e, p, q):
        print("4: Loading facts in updater")
        self.implicit_facts = q.get_all_facts()
        self.explicit_facts = self.__get_explicit_facts(e, q)
        print("5: Loading rules in updater")
        self.old_rules = self.__get_rules(p)
        print("6: Create new edb")
        self.dred_edb = self.__new_edb()
        self.old_predicates = self.dred_edb.get_predicates()
        self.new_edb_facts = {}
        self.random_draw = {}
        self.__add_placeholders()

    def reinitialize(self, explicit_facts, implicit_facts):
        self.implicit_facts = implicit_facts
        self.explicit_facts = explicit_facts
        self.dred_edb = self.__new_edb()
        self.old_predicates = self.dred_edb.get_predicates()
        self.new_edb_facts = {}
        
        self.__add_placeholders()

    def __get_explicit_facts(self, edb, q):
        predicates = edb.get_predicates()

        facts = {}
        for predicate in predicates:
            facts[predicate] = facts[predicate] = self.__term_id_to_name(edb.get_facts(predicate), q)

        return facts

    def __get_rules(self, program):
        rules = []
        n_rules=program.get_n_rules()

        for i in range(n_rules):
            rule_string = program.get_rule(i)
            rules.append(parser.parse_rule(rule_string))
        
        return rules

    def __add_placeholders(self):
        for predicate in self.explicit_facts:
            del_predicate = predicate+ deletion_suffix
            n_terms = len(self.explicit_facts[predicate][0])
            terms = [tuple(placeholder for x in range(n_terms))]
            self.dred_edb.add_csv_source(del_predicate, terms)

    def __term_id_to_name(self, facts, q):
        new_facts = []
        for fact in facts:
            new_facts.append(tuple(q.get_term_name(x) for x in fact))
     
        return new_facts
    
    def __create_copy_rule(self, predicate):
        rule = Rule()
        
        n_terms = len(self.dred_edb.get_facts(predicate)[0])
        terms = ["A" + str(x+1) for x in range(n_terms)]
        head = [Literal(predicate + copy_suffix, terms)]
        rule.set_head(head)

        included = Literal(predicate, terms)
        not_deleted = Literal(predicate+deletion_suffix, terms, is_negated=True)
        rule.set_body([included, not_deleted])

        return rule.str()

    def __create_overdeletion_rules(self, rule):
        overdeletion_rules = []
        body = rule.get_body()
        new_head = rule.get_head()

        # create new head
        for literal in new_head:
            del_name_head = literal.get_predicate_name() + deletion_suffix
            literal.set_predicate_name(del_name_head)

        for literal in body:
            overdeletion_rule = Rule()
            overdeletion_rule.set_head(new_head)
            name_body = literal.get_predicate_name()
            del_name_body = name_body + deletion_suffix

            literal.set_predicate_name(del_name_body)
            overdeletion_rule.set_body(body)
            overdeletion_rules.append(overdeletion_rule.str())

            literal.set_predicate_name(name_body)

        return overdeletion_rules

    def __set_overdeletion_rules(self):
        rules = self.old_rules
        predicates = self.old_predicates

        deletion_rules = []
        for rule in rules:
            deletion_rules.extend(self.__create_overdeletion_rules(rule))
        
        for predicate in predicates:
            deletion_rules.append(self.__create_copy_rule(predicate))

        self.__add_rules(deletion_rules)

    def __create_rederivation_rule(self,rule):
        body = rule.get_body()
        new_head = rule.get_head()
        new_rule = Rule()
        
        for literal in body:
            new_name = literal.get_predicate_name() + copy_suffix
            literal.set_predicate_name(new_name)

        for literal in new_head:
            new_name_head = literal.get_predicate_name() + copy_suffix
            overdeleted_head_name = literal.get_predicate_name() + deletion_suffix
            overdeleted_head = Literal(overdeleted_head_name, literal.get_terms())

            literal.set_predicate_name(new_name_head)
            body.append(overdeleted_head)
            new_rule.set_body(body)
            new_rule.set_head(new_head)

        return new_rule.str()

    def __set_rederivation_rules(self):
        rules = self.old_rules
        rederivation_rules = []

        for rule in rules:
            rederivation_rules.append(self.__create_rederivation_rule(rule))
        
        self.__add_rules(rederivation_rules)

    def __create_insertion_rules(self, rule):
        insertion_rules = []
        body = rule.get_body()
        new_head = rule.get_head()

        for literal in new_head:
            insertion_name_head = literal.get_predicate_name() + insertion_suffix
            literal.set_predicate_name(insertion_name_head)

        new_body = copy.deepcopy(body)

        for literal in new_body:
            new_literal_name = literal.get_predicate_name() + copy_suffix
            literal.set_predicate_name(new_literal_name)
    
        for i, literal in enumerate(new_body):
            insertion_rule = Rule()
            insertion_rule.set_head(new_head)

            insertion_name_literal = body[i].get_predicate_name() + insertion_suffix
            new_body[i].set_predicate_name(insertion_name_literal)

            insertion_rule.set_body(new_body)

            insertion_rules.append(insertion_rule.str())

            new_body[i].set_predicate_name(body[i].get_predicate_name() + copy_suffix)

        return insertion_rules

    def __create_insert_copy_rules(self, rule):
        head = rule.get_head()
        body = rule.get_body()

        insert__copy_rules = set()

        for literal in itertools.chain(head, body):
            rule = Rule()
            predicate = literal.get_predicate_name()
            n_terms  = len(literal.get_terms())
            terms = ["A" + str(x+1) for x in range(n_terms)]

            new_head = [Literal(predicate + copy_suffix, terms)]
            rule.set_head(new_head)

            inserted = [Literal(predicate+insertion_suffix, terms)]
            rule.set_body(inserted)
            insert__copy_rules.add(rule.str())

        return insert__copy_rules

    def __set_insertion_rules(self):
        rules = self.old_rules
        insertion_rules = []
        insertion_copy_rules = set()

        for rule in rules:
            insertion_rules.extend(self.__create_insertion_rules(rule))
            insertion_copy_rules.update(self.__create_insert_copy_rules(rule))
        
        insertion_rules.extend(list(insertion_copy_rules))
        
        self.__add_rules(insertion_rules)

    def __new_edb(self):
        result = glog.EDBLayer()

        all_facts = self.implicit_facts
        predicates_in_both = set(self.implicit_facts).intersection(set(self.explicit_facts))
        predicates_in_explicit_only = set(self.explicit_facts) - set(self.implicit_facts)

        for predicate in predicates_in_both:
            all_facts[predicate] = self.explicit_facts[predicate] + self.implicit_facts[predicate]

        for predicate in predicates_in_explicit_only:
            all_facts[predicate] = self.explicit_facts[predicate]
        for predicate in all_facts:
            result.add_csv_source(predicate, all_facts[predicate])
        
        return result

    def __add_rules(self, rules):
        for rule in rules:
            self.dred_program.add_rule(rule)
    
    def __create_program(self):
        self.dred_program = glog.Program(self.dred_edb)
        self.__set_overdeletion_rules()
        self.__set_rederivation_rules()
        self.__set_insertion_rules()
        
    def insert_facts(self, predicate, terms):
        if predicate in self.new_edb_facts:
            self.new_edb_facts[predicate].extend(terms)
        else:
            self.new_edb_facts[predicate] = terms

        insert_predicate = predicate + insertion_suffix
        self.dred_edb.add_csv_source(insert_predicate, self.new_edb_facts[predicate])
    
    def delete_facts(self, predicate, terms):
        if predicate in self.new_edb_facts:
            self.new_edb_facts[predicate].extend(terms)
        else:
            self.new_edb_facts[predicate] = terms

        insert_predicate = predicate + deletion_suffix
        self.dred_edb.add_csv_source(insert_predicate, self.new_edb_facts[predicate])
    
    def update_facts(self, reinitialize=True):
        self.__create_program()
        r_update= glog.Reasoner(chaseProcedure, self.dred_edb, self.dred_program, typeProv=typeProv, edbCheck=False, queryCont=False)
        stats = r_update.create_model(0)
        tg_update = r_update.get_TG()
        q_update = glog.Querier(tg_update)

        print("DRed update:", stats, '\n')
        updated_facts = {k: v for k, v in q_update.get_all_facts().items() if k.endswith(copy_suffix)}
        
        for key in list(updated_facts):
            updated_facts[key.removesuffix(copy_suffix)] = updated_facts.pop(key)
        
        edb_predicates = list(self.new_edb_facts.keys())
        edb_predicates.extend(list(self.explicit_facts.keys()))
        edb_facts = {key: updated_facts.pop(key) for key in updated_facts.keys() & edb_predicates }

        if reinitialize:
            explicit_facts = copy.deepcopy(edb_facts)
            implicit_facts = copy.deepcopy(updated_facts)
            self.reinitialize(edb_facts, updated_facts)
        
            return explicit_facts, implicit_facts 
        else:
            return edb_facts, updated_facts
            

    def __pick_random_facts(self,n):
        predicates = list(self.explicit_facts.keys())
        n_predicates = len(predicates)
        weight = [len(self.explicit_facts[x]) for x in self.explicit_facts]
        chance = [weight[k]/sum(weight) for k in range(n_predicates)]
        
        predicate_draws = np.random.multinomial(n, chance, size=1)

        for predicate_index, draws in enumerate(predicate_draws[0]):
            if (draws > 0):
                predicate = predicates[predicate_index]
                n_draws = min(len(self.explicit_facts), draws)
                facts = random.sample(self.explicit_facts[predicate], n_draws)
                self.random_draw[predicate] = facts

    def __delete_random_facts(self):
        for predicate in self.random_draw:
            self.delete_facts(predicate, self.random_draw[predicate])
         
    def deletion_benchmark(self,n):
        self.__pick_random_facts(n)
        self.__delete_random_facts()

        (edb_facts, updated_facts) = self.update_facts(reinitialize=False)
        print(updated_facts)
        edb = glog.EDBLayer()
        for predicate in edb_facts:
            edb.add_csv_source(predicate, edb_facts[predicate])
        
        p = glog.Program(edb)
         
        for rule in self.old_rules:
            p.add_rule(rule.str()) 
        
        r = glog.Reasoner(chaseProcedure, edb, p, typeProv=typeProv, edbCheck=False, queryCont=False)
        stats = r.create_model(0)
        print("full materialisation:", stats)


# Initial materialization 
print("1: loading first edb")
edb = glog.EDBLayer(edb_file)
program = glog.Program(edb)
program.load_from_file(rule_location)
r = glog.Reasoner(chaseProcedure, edb, program, typeProv=typeProv, edbCheck=False, queryCont=False)
print("2: start first materialization")
r.create_model(0)
tg = r.get_TG()
q = glog.Querier(tg)

print("3: First Materialization done")


# maintanance
dred_updater = DRed_updater(edb,program,q)

dred_updater.insert_facts("src_A", [("b",)])
dred_updater.delete_facts("src_An", [("b",)])
(edb_update, idb_update) = dred_updater.update_facts()
print(idb_update)



