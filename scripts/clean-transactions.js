const readline = require('readline');
const { PrismaClient } = require('@prisma/client');
require('dotenv').config();

const prisma = new PrismaClient();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

async function cleanTransactions() {
  try {
    // Test connection first
    console.log('Testing database connection...');
    await prisma.$connect();
    console.log('✅ Database connection successful');
    
    console.log('⚠️  WARNING: This will delete ALL transactions from the database!');
    console.log('This will also reset all account balances to their initial values.');
    console.log('This action cannot be undone.');
    
    const answer = await new Promise((resolve) => {
      rl.question('Are you sure you want to proceed? (type "yes" to confirm): ', resolve);
    });
    
    if (answer.toLowerCase() !== 'yes') {
      console.log('Operation cancelled.');
      rl.close();
      return;
    }
    
    const confirmAnswer = await new Promise((resolve) => {
      rl.question('Type "DELETE ALL TRANSACTIONS" to confirm: ', resolve);
    });
    
    if (confirmAnswer !== 'DELETE ALL TRANSACTIONS') {
      console.log('Operation cancelled.');
      rl.close();
      return;
    }
    
    console.log('Starting transaction cleanup...');
    
    // Count existing transactions
    const transactionCount = await prisma.transaction.count();
    
    console.log(`Found ${transactionCount} transactions to delete.`);
    
    if (transactionCount === 0) {
      console.log('No transactions to delete.');
      rl.close();
      return;
    }
    
    // Delete all transactions and reset account balances in a transaction
    await prisma.$transaction(async (tx) => {
      // Delete all transactions
      await tx.transaction.deleteMany({});
      
      // Get all accounts to reset their balances to their initial values
      const accounts = await tx.account.findMany({
        select: { id: true, initialBalance: true },
      });

      const updatePromises = accounts.map((account) =>
        tx.account.update({
          where: { id: account.id },
          data: { balance: account.initialBalance ?? 0 },
        })
      );

      await Promise.all(updatePromises);
    });
    
    console.log(`✅ Successfully deleted ${transactionCount} transactions.`);
    console.log('✅ Reset all account balances to their initial values.');
    console.log('Database cleanup completed.');
    
  } catch (error) {
    if (error.message.includes('connect')) {
      console.error('❌ Database connection failed. Please check your database configuration.');
      console.error('Make sure your .env file has the correct DATABASE_URL.');
    } else {
      console.error('❌ Error cleaning transactions:', error.message);
    }
    process.exit(1);
  } finally {
    rl.close();
    await prisma.$disconnect();
  }
}

// Run the script
cleanTransactions();
