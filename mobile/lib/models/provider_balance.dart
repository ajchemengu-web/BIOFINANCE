/// Mirrors backend/app/schemas/balances.py ProviderBalance.
class ProviderBalance {
  const ProviderBalance({required this.providerCode, required this.amount, this.currency = 'KES'});

  final String providerCode;
  final double amount;
  final String currency;

  factory ProviderBalance.fromJson(Map<String, dynamic> json) => ProviderBalance(
        providerCode: json['provider_code'] as String,
        amount: double.parse(json['amount'].toString()),
        currency: json['currency'] as String? ?? 'KES',
      );
}

class BalancesResult {
  const BalancesResult({required this.total, required this.byProvider, this.currency = 'KES'});

  final double total;
  final String currency;
  final List<ProviderBalance> byProvider;

  factory BalancesResult.fromJson(Map<String, dynamic> json) => BalancesResult(
        total: double.parse(json['total'].toString()),
        currency: json['currency'] as String? ?? 'KES',
        byProvider: (json['by_provider'] as List)
            .map((e) => ProviderBalance.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
