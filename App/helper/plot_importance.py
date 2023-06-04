def plot_variable_importance(models, X_train):
    import matplotlib.pyplot as plt
    from pandas import DataFrame

    for model_name, model in models.items():
        if model_name == 'VotingRegressor':
            for i, m in enumerate(model.estimators_):
                plot_variable_importance({f"Estimator {i}": m}, X_train)
        else:
            if model_name == 'LinearRegression':
                imp = DataFrame({"imp":model.coef_, "names":X_train.columns}).sort_values("imp", ascending=True)
                title = 'Coefficients Plot ' + ' ' + model_name
            elif hasattr(model, "feature_importances_"):
                imp = DataFrame({"imp":model.feature_importances_, "names":X_train.columns}).sort_values("imp", ascending=True)
                title = 'Variable Importance Plot ' + ' ' + model_name
            else:
                print(f"No feature importances or coefficients available for model {model_name}")
                continue

            fig, ax = plt.subplots(figsize=(15, 5), dpi=150)
            ax.barh(imp["names"], imp["imp"], color="green")
            ax.set_xlabel('\nVariable Importance/Coefficients')
            ax.set_ylabel('Features\n')
            ax.set_title(title + '\n')
            plt.show()