import numpy as np
import scipy.stats


def likelihood_ratio_test(
    ll_full: np.ndarray, 
    ll_reduced: np.ndarray, 
    df_full: int, 
    df_reduced: int
    ):
    """
    Perform log-likihood ratio test based on already fitted models.

    The reduced model has to be nested within the full model
    for the deviance to be chi-square distributed under the null
    hypothesis: The p-values are incorrect if the models are not nested.

    :param ll_full: np.array (genes)
        Likelihood of full model for each gene.
    :param ll_reduced:  np.array (genes)
        Likelihood of reduced model for each gene.
    :param df_full: int
        Degrees of freedom (number of parameters) of full model for each gene.
    :param df_reduced:  int
        Degrees of freedom (number of parameters) of reduced model for each gene.
    """
    if ll_full.shape[0] != ll_full.shape[0]:
        raise ValueError('stats.likelihood_ratio_test(): ll_full and ll_red have to contain the same number of genes')
    # Compute the difference in degrees of freedom.
    delta_df = df_full - df_reduced
    # Compute the deviance test statistic.
    delta_dev = 2 * (ll_full - ll_reduced)
    # Compute the p-values based on the deviance and its expection based on the chi-square distribution.
    pvals = 1 - scipy.stats.chi2(delta_df).cdf(delta_dev)
    return pvals


def wilcoxon(
    x0: np.ndarray,
    x1: np.ndarray,
    ):
    """
    Perform Wilcoxon rank sum test (Mann-Whiteney U test) along second axis
    (for each gene).

    The Wilcoxon rank sum test is a non-parameteric test
    to compare two groups of observations.

    :param x0: np.array (observations x genes)
        Observations in first group by gene
    :param x1:  np.array (observations x genes)
        Observations in second group by gene.
    """
    axis = 1
    if np.any(np.ndim(x0) != np.ndim(x1)):
        raise ValueError('stats.wilcoxon(): number of dimensions is not allowed to differ between x0 and x1!')
    # Reshape into 2D array if only one test is performed.
    if np.ndim(x0)==1:
        x0 = x0.reshape([x0.shape[0], 1])
        x1 = x1.reshape([x1.shape[0], 1])
    if np.any(x0.shape[axis] != x1.shape[axis]):
        raise ValueError('stats.wilcoxon(): the first axis (number of tests) is not allowed to differ between x0 and x1!')

    pvals = np.asarray([scipy.stats.mannwhitneyu(x=x0[:, i].flatten(), y=x1[:, i].flatten(), 
        alternative='two-sided').pvalue for i in range(x0.shape[1])])
    return pvals


def t_test_raw(
    x0: np.ndarray,
    x1: np.ndarray,
    ):
    """
    Perform two-sided t-test allowing for unequal group variances (Welch's t-test) on raw data
    along second axis (for each gene).

    The t-test assumes normally distributed data. This function computes
    the necessary statistics and calls t_test_moments().

    :param x0: np.array (observations x genes)
        Observations in first group by gene
    :param x1:  np.array (observations x genes)
        Observations in second group by gene.
    """
    axis = 1
    if x0.shape[1] != x1.shape[1]:
        raise ValueError('stats.t_test_raw(): x0 and x1 have to contain the same number of genes')
    # Reshape into 2D array if only one test is performed.
    if np.ndim(x0)==1:
        x0 = x0.reshape([x0.shape[0], 1])
        x1 = x1.reshape([x1.shape[0], 1])
    if np.any(x0.shape[axis] != x1.shape[axis]):
        raise ValueError('stats.wilcoxon(): the first axis (number of tests) is not allowed to differ between x0 and x1!')

    mu0 = np.mean(x0, axis=0).flatten()
    var0 = np.var(x0, axis=0).flatten()
    mu1 = np.mean(x1, axis=0).flatten()
    var1 = np.var(x1, axis=0).flatten()
    n0 = x0.shape[0]
    n1 = x1.shape[0]

    pval = t_test_moments(mu0=mu0, mu1=mu1, var0=var0, var1=var1, n0=n0, n1=n1)
    return pval


def t_test_moments(
    mu0: np.ndarray, 
    mu1: np.ndarray, 
    var0: np.ndarray, 
    var1: np.ndarray, 
    n0: int, 
    n1: int
    ):
    """
    Perform two-sided t-test allowing for unequal group variances (Welch's t-test)
    moments of distribution of data.

    The t-test assumes normally distributed data.

    :param mu0: np.array (genes)
        Mean expression by gene of first group.
    :param mu1 np.array (genes)
        Mean expression by gene of second group.
    :param var0: np.array (genes)
        Variance of expression by gene of first group.
    :param var1 np.array (genes)
        Variance of expression by gene of second group.
    :param n0: np.array (genes)
        Number of observations in first group.
    :param n1 np.array (genes)
        Number of observations in second group.
    """
    if len(mu0) != len(mu1):
        raise ValueError('stats.t_test_moments(): mu and mu1 have to contain the same number of entries')
    if len(var0) != len(var1):
        raise ValueError('stats.t_test_moments(): mu and mu1 have to contain the same number of entries')

    s_delta = np.sqrt((var0 / n0) + (var1 / n1))
    t = (mu0 - mu1) / s_delta

    df = (
            np.square((var0 / n0) + (var1 / n1)) /
            (
                    (np.square(var0 / n0) / (n0 - 1)) +
                    (np.square(var1 / n1) / (n1 - 1))
            )
    )

    pval = 1 - scipy.stats.t(df).cdf(t)
    return pval


def wald_test(
    theta_mle: np.ndarray, 
    theta_sd: np.ndarray, 
    theta0: int = 0):
    """
    Perform single coefficient Wald test.

    The Wald test unit_test whether a given coefficient deviates significantly
    from the supplied reference value, based on the standard deviation
    of the posterior of the parameter estimate. In the context of
    generalized linear nodels, this standard deviation
    is typically obtained via the hessian at the maximum likelihood
    estimator, which is an approximation of the fisher information matrix,
    based on which the parameter covariance matrix can be calculated,
    which has the standard deviation of each the distribution of each
    parameter on its diagonal.

    :param theta_mle: np.array (genes)
        Maximum likelihood estimator of given parameter by gene.
    :param theta_sd:  np.array (genes)
        Standard deviation of maximum likelihood estimator of given parameter by gene.
    :param theta0: float
        Reference parameter values against which coefficient is tested.
    """
    if theta_mle.shape[0] != theta_sd.shape[0]:
        raise ValueError('stats.wald_test(): theta_mle and theta_sd have to contain the same number of entries')

    wald_statistic = (theta_mle - theta0) / theta_sd
    pvals = 1 - scipy.stats.norm(loc=0, scale=1).cdf(wald_statistic)  # check whether this is two-sided
    return pvals


def two_coef_z_test(
    theta_mle0: np.ndarray, 
    theta_mle1: np.ndarray, 
    theta_sd0: np.ndarray, 
    theta_sd1: np.ndarray
    ):
    """
    Perform z-test to compare two coefficients.

    The Wald test unit_test whether a given coefficient deviates significantly
    from the other ceofficient, based on their standard deviations
    of the posterior of the parameter estimates. In the context of
    generalized linear nodels, this standard deviation
    is typically obtained via the hessian at the maximum likelihood
    estimator, which is an approximation of the fisher information matrix,
    based on which the parameter covariance matrix can be calculated,
    which has the standard deviation of each the distribution of each
    parameter on its diagonal.

    :param theta_mle0: np.array (genes)
        Maximum likelihood estimator of first parameter by gene.
    :param theta_mle1: np.array (genes)
        Maximum likelihood estimator of second parameter by gene.
    :param theta_sd0:  np.array (genes)
        Standard deviation of maximum likelihood estimator of first parameter by gene.
    :param theta_sd1:  np.array (genes)
        Standard deviation of maximum likelihood estimator of second parameter by gene.
    """
    if theta_mle0.shape[0] != theta_mle1.shape[0]:
        raise ValueError(
            'stats.two_coef_z_test(): theta_mle0 and theta_mle1 have to contain the same number of entries')
    if theta_sd0.shape[0] != theta_sd1.shape[0]:
        raise ValueError('stats.two_coef_z_test(): theta_sd0 and theta_sd1 have to contain the same number of entries')
    if theta_mle0.shape[0] != theta_sd0.shape[0]:
        raise ValueError('stats.two_coef_z_test(): theta_mle0 and theta_sd0 have to contain the same number of entries')

    z_statistic = (theta_mle0 - theta_mle1) / np.sqrt(np.square(theta_sd0) + np.square(theta_sd1))
    pvals = 1 - scipy.stats.norm(loc=0, scale=1).cdf(z_statistic)  # check whether this is two-sided
    return pvals
