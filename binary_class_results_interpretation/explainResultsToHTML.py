#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 13:55:02 2020

@author: anton
"""

import shap
import matplotlib.pyplot as plt
import numpy as np
import operator

class ExplainResultsToHTML():
    '''
    Results interpretation of binary classification task by SHAP library
    
    Attributes
    ----------
    model:
        trained model on train dataset
    model_type: str
        model type like 'linear'', 'tree-based' or 'neural-net'
    is_proba: bool
        flag for return probabilities on plot or raw SHAP-values
    scaler:
        scaler for inverse features values on plot (default None)
    
    Methods
    -------
    __explainer()
        Creation explainer
    __shap_values(X_test)
        Calculation SHAP values
    single_plot()
        Plot individual SHAP value for observation and save as .html
    '''

    def __init__(self, model, X_train, model_type, is_proba, scaler=None):
        '''
        Parameters
        ----------
        model:
            trained model on train dataset
        model_type: str
            model type like 'linear'', 'tree-based' or 'neural-net'
        is_proba: bool
            flag for return probabilities on plot or raw SHAP-values
        scaler:
            scaler for inverse features values on plot (default None)
        '''
        self.model = model
        self.X_train = X_train
        self.model_type = model_type
        self.is_proba = is_proba
        self.scaler = scaler


    def __explainer(self):
        '''
        Creation explainer
        
        '''
        if self.model_type == 'linear':
            explainer = shap.LinearExplainer(self.model,
                                             self.X_train,
                                            )
        if self.model_type == 'tree_based':
            explainer = shap.TreeExplainer(self.model,
                                           self.X_train,
                                          )
        if self.model_type == 'neural_net':
            explainer = shap.DeepExplainer(self.model,
                                           self.X_train,
                                          )
        return explainer
    
    
    def __shap_values(self, X_test):
        '''
        Calculation SHAP values
                
        Parameters
        ----------
        X_test : numpy.ndarray
            one test data example
        '''
        explainer_ = self.__explainer()
        return explainer_.shap_values(X_test)
   

    def single_plot(self, features_list, one_row, path_save="single_plot.html"):
        '''
        Plot individual SHAP value for observation and save as .html
        
        Parameters
        ----------
        features_list : list
            list of features names
        one_row : numpy.ndarray
            one test data example
        '''
        link_ = 'logit' if self.is_proba else 'identity'
        features_ = one_row if self.scaler is None else self.scaler.inverse_transform(one_row)
        single_plot = shap.force_plot(base_value=self.__explainer().expected_value, 
                                      shap_values=self.__shap_values(one_row),
                                      features=features_,
                                      feature_names=features_list,
                                      show=False,
                                      matplotlib=False,
                                      link=link_,
                                     )
        shap.save_html(path_save, single_plot)
    
    
    def summary_plot(self, features_list, X_test, path_save="summary_plot.html", is_bar=False):
        '''
        Summary plot SHAP value for features and save as .jpeg
        
        Parameters
        ----------
        features_list : list
            list of features names
        X_test : numpy.ndarray
            test data
        is_bar : bool
            bar or dot flag
        '''
        plot_type = 'bar'if is_bar else 'dot'
        summary_plot = shap.summary_plot(self.__shap_values(X_test),
                                         X_test,
                                         max_display=len(features_list),
                                         feature_names=features_list,
                                         plot_type=plot_type,
                                         show=False,
                                        )
        plt.savefig('summary_plot.jpeg', bbox_inches='tight')


    def get_impact_of_n_max_shap_values(self, one_row, features_list, n_max, is_pos):
        '''
        Get impact of each top n_max features in percent
        of impact of all features on positive and negative classes 
        
        Parameters
        ----------
        one_row : numpy.ndarray
            one test data example
        features_list : list
            list of features names
        n_max : int
            number of most important features
        is_pos : bool
            positive or negative class
        '''
        shap = self.__shap_values(one_row)
        shap_dict = dict(zip(features_list,
                             shap,
                             ),
                         )
        shap_pos_sum = np.sum(shap[np.where(shap > 0)])
        shap_neg_sum = np.sum(shap[np.where(shap < 0)])
        
        shap_dict_pos = {}
        shap_dict_neg = {}
        
        for key, value in shap_dict.items():
            if shap_dict[key] > 0:
                shap_dict_pos.update({key: value / shap_pos_sum})
            if shap_dict[key] < 0:
                shap_dict_neg.update({key: value / shap_neg_sum})
        if is_pos:
            return dict(sorted(shap_dict_pos.items(), key = operator.itemgetter(1), reverse=True)[:n_max])
        else:
            return dict(sorted(shap_dict_neg.items(), key = operator.itemgetter(1), reverse=True)[:n_max])
        