class ProviderBalance {
  const ProviderBalance({
    required this.providerCode,
    required this.displayName,
    required this.amount,
    this.currency = 'KES',
  });

  final String providerCode;
  final String displayName;
  final double amount;
  final String currency;
}
